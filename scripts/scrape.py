#!/usr/bin/env python3
"""
GSAU.gg Price Scraper
Fetches product data from multiple e-commerce platforms and outputs combined JSON.

Usage:
    python scrape.py           # Normal mode: fetch from stores
    python scrape.py --offline # Offline mode: use cached raw data
"""

import argparse
import ipaddress
import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urlparse

# Configure logging for fetchers
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Import from local modules
from config import (
    STORES_FILE, RAW_DATA_DIR, PROJECT_ROOT,
    MAX_WORKERS, FUTURE_TIMEOUT
)
from fetchers import get_fetcher
from log_collector import get_collector, get_store_logs
from validators import get_validator
from normalizers import get_normalizer
from utils import count_in_stock, build_error_stats
from matching import match_items, get_match_stats
from item_history import (
    load_history as load_item_history,
    save_history as save_item_history,
    track_items,
    prune_old_entries,
    cleanup_orphaned_items,
    ITEM_HISTORY_FILE,
)
from generate_frontend import generate_frontend_data

# Initialize log collector
log_collector = get_collector()

# Data file paths
DATA_DIR = PROJECT_ROOT / "public" / "data"
ITEMS_FILE = DATA_DIR / "items.json"
MATCHES_FILE = DATA_DIR / "matches.json"
STATS_FILE = DATA_DIR / "stats.json"

# Thread-safe printing
_print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print function."""
    with _print_lock:
        print(*args, **kwargs)


def get_cache_path(store_name: str) -> str:
    """Get the cache file path for a store."""
    # Sanitize store name for filename
    safe_name = re.sub(r'[^\w\-]', '_', store_name.lower())
    return RAW_DATA_DIR / f"{safe_name}.json"


def save_raw_data(store_name: str, platform: str, raw_products: list):
    """Save raw product data to cache."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = get_cache_path(store_name)
    cache_data = {
        "store_name": store_name,
        "platform": platform,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "products": raw_products
    }
    with open(cache_path, "w") as f:
        json.dump(cache_data, f)


def load_raw_data(store_name: str) -> dict | None:
    """Load raw product data from cache. Returns None if not cached."""
    cache_path = get_cache_path(store_name)
    if not cache_path.exists():
        return None
    with open(cache_path, "r") as f:
        return json.load(f)


def is_safe_url(url: str) -> bool:
    """Validate URL is safe (not a private/local IP) to prevent SSRF attacks."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False

        # Block localhost and common local names
        if hostname in ('localhost', '127.0.0.1', '::1', '0.0.0.0'):
            return False

        # Block private IP ranges
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                return False
        except ValueError:
            # Not an IP address, likely a domain name - that's fine
            pass

        # Require https or http scheme
        if parsed.scheme not in ('http', 'https'):
            return False

        return True
    except Exception:
        return False


def load_stores():
    """Load store configuration from stores.json."""
    with open(STORES_FILE, "r") as f:
        data = json.load(f)

    stores = []
    for s in data["stores"]:
        if not s.get("enabled", True):
            continue

        url = s.get("url", "")
        if not is_safe_url(url):
            safe_print(f"  Warning: Skipping store '{s.get('name', 'unknown')}' - invalid or unsafe URL")
            continue

        stores.append(s)

    return stores


def filter_and_normalize(
    raw_products: list, platform: str, store_name: str, base_url: str, store_id: str
) -> tuple[list, int, list]:
    """Filter and normalize products using platform-specific validator/normalizer.

    Returns (items_list, filtered_count, filtered_products_details).
    Items are at variant level with composite IDs (storeId|productId|variantId).
    """
    validator = get_validator(platform)
    normalizer = get_normalizer(platform, store_name, base_url, store_id)

    items = []
    filtered_count = 0
    filtered_products = []

    for product in raw_products:
        if validator.is_valid(product):
            # Use normalize_all to get variant-level items
            normalized_items = normalizer.normalize_all(product)
            items.extend(normalized_items)
        else:
            filtered_count += 1
            # Capture why this product was filtered
            reason = validator.get_exclusion_reason(product)
            if reason:
                filtered_products.append({
                    "title": reason["title"],
                    "reason": reason["type"],
                    "keyword": reason["keyword"],
                    "filterCategory": reason["category"],
                })

    return items, filtered_count, filtered_products


def fetch_store_products(store: dict) -> tuple[list, dict]:
    """Fetch products using the appropriate fetcher. Returns (items, stats)."""
    store_name = store["name"]
    store_id = store.get("id", store_name.lower().replace(" ", "-"))
    base_url = store["url"].rstrip("/")
    platform = store.get("platform", "shopify")

    # Use the fetcher to get raw products
    fetcher = get_fetcher(platform, store_name, base_url)
    raw_products, stats = fetcher.fetch()

    # Only save to cache if fetch was successful (has products, no error)
    if raw_products and not stats.get("error"):
        save_raw_data(store_name, platform, raw_products)

    # Filter and normalize to items (variant-level)
    items, filtered_count, filtered_products = filter_and_normalize(
        raw_products, platform, store_name, base_url, store_id
    )

    # Update stats with filtering info
    in_stock = count_in_stock(items)
    stats["filtered"] = filtered_count
    stats["filteredProducts"] = filtered_products
    stats["final"] = len(items)
    stats["inStock"] = in_stock
    stats["outOfStock"] = len(items) - in_stock

    # Attach logs for this store
    stats["logs"] = get_store_logs(store_name)

    return items, stats


def process_cached_products(store: dict, max_age_hours: float | None = None) -> tuple[list, dict]:
    """Process products from cache. Returns (items, stats).

    Args:
        store: Store configuration dict
        max_age_hours: Maximum cache age in hours. If None, any age is accepted.
    """
    store_name = store["name"]
    store_id = store.get("id", store_name.lower().replace(" ", "-"))
    base_url = store["url"].rstrip("/")
    platform = store.get("platform", "shopify")
    start_time = time.time()

    safe_print(f"Processing cached {store_name}...")

    # Load from cache
    cache_data = load_raw_data(store_name)
    if not cache_data:
        safe_print(f"  No cache found for {store_name}")
        return [], {
            "name": store_name,
            "url": base_url,
            "platform": platform,
            "fetched": 0,
            "filtered": 0,
            "filteredProducts": [],
            "final": 0,
            "inStock": 0,
            "outOfStock": 0,
            "error": "No cache found",
            "duration": 0,
            "logs": []
        }

    # Check cache age if max_age specified
    if max_age_hours is not None:
        fetched_at = cache_data.get("fetched_at")
        if fetched_at:
            cache_time = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - cache_time).total_seconds() / 3600
            if age_hours > max_age_hours:
                safe_print(f"  Cache too old ({age_hours:.1f}h > {max_age_hours}h)")
                return [], {
                    "name": store_name,
                    "url": base_url,
                    "platform": platform,
                    "fetched": 0,
                    "filtered": 0,
                    "filteredProducts": [],
                    "final": 0,
                    "inStock": 0,
                    "outOfStock": 0,
                    "error": f"Cache too old ({age_hours:.1f}h)",
                    "duration": 0,
                    "logs": []
                }

    raw_products = cache_data.get("products", [])

    # Filter and normalize to items (variant-level)
    items, filtered_count, filtered_products = filter_and_normalize(
        raw_products, platform, store_name, base_url, store_id
    )

    duration = time.time() - start_time
    in_stock = count_in_stock(items)
    safe_print(f"  Processed: {len(items)} items ({filtered_count} filtered)")

    stats = {
        "name": store_name,
        "url": base_url,
        "platform": platform,
        "fetched": len(raw_products),
        "filtered": filtered_count,
        "filteredProducts": filtered_products,
        "final": len(items),
        "inStock": in_stock,
        "outOfStock": len(items) - in_stock,
        "error": None,
        "duration": round(duration, 2),
        "cached_at": cache_data.get("fetched_at"),
        "logs": [{"time": "cache", "level": "INFO", "message": f"Loaded from cache ({cache_data.get('fetched_at', 'unknown')})"}]
    }
    return items, stats


def main():
    """Main scraper function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="GSAU.gg Price Scraper")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use cached raw data instead of fetching from stores"
    )
    args = parser.parse_args()

    print("=" * 50)
    print("GSAU.gg Price Scraper")
    if args.offline:
        print("(OFFLINE MODE - using cached data)")
    print("=" * 50)

    scrape_start = time.time()

    # Load stores
    stores = load_stores()
    if not stores:
        print("No enabled stores found in stores.json")
        return

    print(f"Found {len(stores)} enabled store(s)")
    if args.offline:
        print("Processing cached data...")
    else:
        # Separate Shopify stores (run sequentially due to shared rate limit)
        shopify_stores = [s for s in stores if s.get("platform", "shopify") == "shopify"]
        other_stores = [s for s in stores if s.get("platform", "shopify") != "shopify"]
        print(f"Fetching {len(shopify_stores)} Shopify stores sequentially, "
              f"{len(other_stores)} others in parallel...")
    print()

    # Fetch or process all products in parallel
    all_products = []
    store_stats = []

    # Choose the processing function based on mode
    process_func = process_cached_products if args.offline else fetch_store_products

    # In online mode, run Shopify stores sequentially to avoid shared rate limits
    if not args.offline:
        shopify_stores = [s for s in stores if s.get("platform", "shopify") == "shopify"]
        other_stores = [s for s in stores if s.get("platform", "shopify") != "shopify"]

        # Process Shopify stores one at a time
        for store in shopify_stores:
            try:
                products, stats = process_func(store)
                # On any error, try cache fallback (even with partial data)
                if stats.get("error"):
                    safe_print(f"  {store['name']} failed: {stats['error']}")
                    cached_products, cached_stats = process_cached_products(store, max_age_hours=24)
                    if cached_products:
                        cached_stats["warning"] = f"Using cache: {stats['error']}"
                        cached_stats["error"] = None
                        all_products.extend(cached_products)
                        store_stats.append(cached_stats)
                        continue
                all_products.extend(products)
                store_stats.append(stats)
            except Exception as e:
                safe_print(f"  Error fetching {store['name']}: {e}")
                cached_products, cached_stats = process_cached_products(store, max_age_hours=24)
                if cached_products:
                    cached_stats["warning"] = f"Using cache: {e}"
                    cached_stats["error"] = None
                    all_products.extend(cached_products)
                    store_stats.append(cached_stats)
                else:
                    store_stats.append(build_error_stats(
                        store["name"], store["url"], store.get("platform", "unknown"),
                        str(e)
                    ))

        # Process other platforms in parallel
        stores_to_process = other_stores
    else:
        stores_to_process = stores

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all store fetches/processing
        future_to_store = {
            executor.submit(process_func, store): store
            for store in stores_to_process
        }

        # Collect results as they complete
        for future in as_completed(future_to_store):
            store = future_to_store[future]
            try:
                products, stats = future.result(timeout=FUTURE_TIMEOUT)
                # On any error, try cache fallback (even with partial data)
                if stats.get("error") and not args.offline:
                    safe_print(f"  {store['name']} failed: {stats['error']}")
                    cached_products, cached_stats = process_cached_products(store, max_age_hours=24)
                    if cached_products:
                        cached_stats["warning"] = f"Using cache: {stats['error']}"
                        cached_stats["error"] = None
                        all_products.extend(cached_products)
                        store_stats.append(cached_stats)
                        continue
                all_products.extend(products)
                store_stats.append(stats)
            except TimeoutError:
                error_msg = f"Timeout after {FUTURE_TIMEOUT}s"
                safe_print(f"  Timeout fetching {store['name']} (exceeded {FUTURE_TIMEOUT}s)")
                # Try cache fallback (max 24h old)
                cached_products, cached_stats = process_cached_products(store, max_age_hours=24)
                if cached_products:
                    cached_stats["warning"] = f"Using cache: {error_msg}"
                    cached_stats["error"] = None
                    all_products.extend(cached_products)
                    store_stats.append(cached_stats)
                else:
                    store_stats.append(build_error_stats(
                        store["name"], store["url"], store.get("platform", "unknown"),
                        error_msg, duration=FUTURE_TIMEOUT
                    ))
            except Exception as e:
                action = "processing" if args.offline else "fetching"
                safe_print(f"  Error {action} {store['name']}: {e}")
                # Try cache fallback (max 24h old) - skip in offline mode
                if not args.offline:
                    cached_products, cached_stats = process_cached_products(store, max_age_hours=24)
                    if cached_products:
                        cached_stats["warning"] = f"Using cache: {e}"
                        cached_stats["error"] = None
                        all_products.extend(cached_products)
                        store_stats.append(cached_stats)
                        continue
                store_stats.append(build_error_stats(
                    store["name"], store["url"], store.get("platform", "unknown"),
                    str(e)
                ))

    # Note: all_products is now a list of items (variant-level)
    all_items = all_products  # Rename for clarity
    raw_count = len(all_items)
    total_fetched = sum(s["fetched"] for s in store_stats)

    # Convert items list to dict (keyed by item_id)
    print()
    print("Building items dict...")
    items_dict = {}
    for item in all_items:
        item_id = item.get("id")
        if item_id:
            items_dict[item_id] = item
    print(f"  {raw_count} items from all stores")

    # Match items across stores (SKU + fuzzy title)
    print()
    print("Matching items across stores...")
    matches = match_items(items_dict)
    match_stats = get_match_stats(matches)
    print(f"  {len(items_dict)} items -> {len(matches)} product groups")
    print(f"  SKU matches: {match_stats['sku_matched']}, "
          f"Title matches: {match_stats['title_matched']}")
    print(f"  Cross-store: {match_stats['multi_vendor']}, "
          f"Single-store: {match_stats['single_vendor']}")

    scrape_duration = time.time() - scrape_start
    last_updated = datetime.now(timezone.utc).isoformat()

    # Track item-level price history
    print()
    print("Tracking price changes...")
    history_data = load_item_history()
    price_stats = track_items(items_dict, history_data)
    prune_old_entries(history_data)
    cleanup_orphaned_items(history_data, set(items_dict.keys()))
    save_item_history(history_data)
    print(f"  {price_stats['new']} new, {price_stats['changed']} changed, "
          f"{price_stats['unchanged']} unchanged")

    # Generate frontend files (products.json, price-history.json)
    print()
    print("Generating frontend data...")
    products, _ = generate_frontend_data(
        items_dict, matches, history_data, last_updated, len(stores)
    )

    # Calculate stock totals from products
    total_in_stock = count_in_stock(products)
    total_out_of_stock = len(products) - total_in_stock

    # Save items.json and matches.json (internal format)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    items_output = {
        "lastUpdated": last_updated,
        "items": items_dict,
    }
    with open(ITEMS_FILE, "w") as f:
        json.dump(items_output, f, separators=(",", ":"))

    matches_output = {
        "lastUpdated": last_updated,
        "matches": matches,
    }
    with open(MATCHES_FILE, "w") as f:
        json.dump(matches_output, f, separators=(",", ":"))

    # Build and save stats output
    stats_output = {
        "lastUpdated": last_updated,
        "duration": round(scrape_duration, 2),
        "stores": store_stats,
        "totals": {
            "rawProducts": total_fetched,
            "afterFilter": raw_count,
            "uniqueItems": len(items_dict),
            "productGroups": len(matches),
            "skuMatched": match_stats["sku_matched"],
            "titleMatched": match_stats["title_matched"],
            "multiVendor": match_stats["multi_vendor"],
            "inStock": total_in_stock,
            "outOfStock": total_out_of_stock,
        },
        "priceHistory": price_stats,
    }
    with open(STATS_FILE, "w") as f:
        json.dump(stats_output, f, indent=2)

    print()
    print("=" * 50)
    print(f"Done! {len(items_dict)} items -> {len(matches)} products -> {len(products)} unique")
    print(f"Stats saved to {STATS_FILE}")
    print(f"Item history saved to {ITEM_HISTORY_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    main()
