#!/usr/bin/env python3
"""
GSAU.gg Price Scraper
Fetches product data from multiple e-commerce platforms and outputs combined JSON.

Usage:
    python scrape.py           # Normal mode: fetch from stores
    python scrape.py --offline # Offline mode: use cached raw data
"""

import argparse
import hashlib
import ipaddress
import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urlparse
from rapidfuzz import fuzz, process

# Configure logging for fetchers
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Import from local modules
from config import (
    STORES_FILE, OUTPUT_FILE, STATS_FILE, RAW_DATA_DIR, HISTORY_FILE,
    FUZZY_THRESHOLD, MAX_WORKERS, FUTURE_TIMEOUT, MAX_TAGS, MAX_ID_LENGTH
)
from fetchers import get_fetcher
from log_collector import get_collector, get_store_logs
from validators import get_validator
from normalizers import get_normalizer
from utils import count_in_stock, build_error_stats
from price_history import (
    load_history, save_history, track_price_changes,
    prune_old_entries, cleanup_orphaned_products
)

# Initialize log collector
log_collector = get_collector()

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


def filter_and_normalize(raw_products: list, platform: str, store_name: str, base_url: str) -> tuple[list, int, list]:
    """Filter and normalize products using platform-specific validator/normalizer.

    Returns (normalized_products, filtered_count, filtered_products_details).
    """
    validator = get_validator(platform)
    normalizer = get_normalizer(platform, store_name, base_url)

    products = []
    filtered_count = 0
    filtered_products = []

    for product in raw_products:
        if validator.is_valid(product):
            normalized = normalizer.normalize(product)
            if normalized:
                products.append(normalized)
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

    return products, filtered_count, filtered_products


def fetch_store_products(store: dict) -> tuple[list, dict]:
    """Fetch products using the appropriate fetcher. Returns (products, stats)."""
    store_name = store["name"]
    base_url = store["url"].rstrip("/")
    platform = store.get("platform", "shopify")

    # Use the fetcher to get raw products
    fetcher = get_fetcher(platform, store_name, base_url)
    raw_products, stats = fetcher.fetch()

    # Save raw products to cache
    save_raw_data(store_name, platform, raw_products)

    # Filter and normalize products
    products, filtered_count, filtered_products = filter_and_normalize(raw_products, platform, store_name, base_url)

    # Update stats with filtering info
    in_stock = count_in_stock(products)
    stats["filtered"] = filtered_count
    stats["filteredProducts"] = filtered_products
    stats["final"] = len(products)
    stats["inStock"] = in_stock
    stats["outOfStock"] = len(products) - in_stock

    # Attach logs for this store
    stats["logs"] = get_store_logs(store_name)

    return products, stats


def process_cached_products(store: dict) -> tuple[list, dict]:
    """Process products from cache. Returns (products, stats)."""
    store_name = store["name"]
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

    raw_products = cache_data.get("products", [])

    # Filter and normalize products
    products, filtered_count, filtered_products = filter_and_normalize(raw_products, platform, store_name, base_url)

    duration = time.time() - start_time
    in_stock = count_in_stock(products)
    safe_print(f"  Processed: {len(products)} products ({filtered_count} filtered)")

    stats = {
        "name": store_name,
        "url": base_url,
        "platform": platform,
        "fetched": len(raw_products),
        "filtered": filtered_count,
        "filteredProducts": filtered_products,
        "final": len(products),
        "inStock": in_stock,
        "outOfStock": len(products) - in_stock,
        "error": None,
        "duration": round(duration, 2),
        "cached_at": cache_data.get("fetched_at"),
        "logs": [{"time": "cache", "level": "INFO", "message": f"Loaded from cache ({cache_data.get('fetched_at', 'unknown')})"}]
    }
    return products, stats


def normalize_title(title: str) -> str:
    """Normalize title for matching - strips colors, punctuation, etc."""
    title = title.lower().strip()
    # Remove common color suffixes
    title = re.sub(r'\s*[-–]\s*(black|tan|od|green|fde|grey|gray|white|red|blue|pink|orange|camo|multicam)\s*$', '', title, flags=re.IGNORECASE)
    # Remove punctuation except hyphens in product codes
    title = re.sub(r'[^\w\s-]', '', title)
    # Normalize whitespace
    title = re.sub(r'\s+', ' ', title)
    return title.strip()


def generate_product_id(normalized_title: str) -> str:
    """Generate a unique product ID from normalized title.

    If the title is longer than MAX_ID_LENGTH, appends a short hash
    to ensure uniqueness while keeping the ID readable.
    """
    base_id = normalized_title.replace(" ", "-")

    if len(base_id) <= MAX_ID_LENGTH:
        return base_id

    # Truncate and add hash suffix for uniqueness
    hash_suffix = hashlib.md5(normalized_title.encode()).hexdigest()[:8]
    # Leave room for dash and 8-char hash
    truncated = base_id[:MAX_ID_LENGTH - 9]
    return f"{truncated}-{hash_suffix}"


def find_matching_group(title: str, grouped: dict, grouped_keys: list) -> str | None:
    """Find existing group that fuzzy-matches this title.

    Uses RapidFuzz's optimized extractOne for O(N) instead of manual O(N) loop,
    with significant constant-factor speedup from C extensions.
    """
    normalized = normalize_title(title)

    # First try exact match (fast path - O(1) dict lookup)
    if normalized in grouped:
        return normalized

    # No keys to match against
    if not grouped_keys:
        return None

    # Use RapidFuzz's optimized extractOne (C extension, early termination)
    result = process.extractOne(
        normalized,
        grouped_keys,
        scorer=fuzz.ratio,
        score_cutoff=FUZZY_THRESHOLD
    )

    return result[0] if result else None


def consolidate_products(products: list) -> list:
    """Group products by title (with fuzzy matching), combining vendor info."""
    grouped = {}
    grouped_keys = []  # Maintain list for efficient fuzzy matching
    fuzzy_matches = 0

    # Sort products for deterministic fuzzy matching (prevents vendor flip-flopping)
    sorted_products = sorted(products, key=lambda p: (normalize_title(p["title"]), p["vendor"]))

    for product in sorted_products:
        normalized = normalize_title(product["title"])

        # Find matching group (exact or fuzzy)
        match_key = find_matching_group(product["title"], grouped, grouped_keys)

        if match_key is None:
            # New product group
            key = normalized
            grouped[key] = {
                "id": generate_product_id(key),
                "title": product["title"],
                "image": product["image"],
                "category": product["category"],
                "tags": list(set(product.get("tags", [])))[:MAX_TAGS],
                "vendors": []
            }
            grouped_keys.append(key)  # Track for fuzzy matching
        else:
            key = match_key
            if key != normalized:
                fuzzy_matches += 1

        # Add vendor info (skip if this vendor already exists for this product)
        existing_vendors = [v["name"] for v in grouped[key]["vendors"]]
        if product["vendor"] not in existing_vendors:
            grouped[key]["vendors"].append({
                "name": product["vendor"],
                "price": product["price"],
                "comparePrice": product.get("comparePrice"),
                "url": product["url"],
                "inStock": product["inStock"]
            })

        # Use image if current is None
        if grouped[key]["image"] is None and product["image"]:
            grouped[key]["image"] = product["image"]

        # Use category from other store if current is Uncategorized
        if grouped[key]["category"] == "Uncategorized" and product["category"] != "Uncategorized":
            grouped[key]["category"] = product["category"]

        # Merge tags
        grouped[key]["tags"] = list(set(grouped[key]["tags"] + product.get("tags", [])))[:MAX_TAGS]

    safe_print(f"  Fuzzy matches found: {fuzzy_matches}")

    # Calculate lowest price and stock status
    result = []
    for item in grouped.values():
        # Skip products with no vendors (shouldn't happen, but guard against it)
        if not item["vendors"]:
            continue

        # Sort vendors: in-stock first, then by price
        item["vendors"].sort(key=lambda v: (not v["inStock"], v["price"]))

        # Get all valid prices (non-None, positive)
        all_prices = [v["price"] for v in item["vendors"] if v["price"] is not None and v["price"] > 0]
        in_stock_prices = [v["price"] for v in item["vendors"] if v["inStock"] and v["price"] is not None and v["price"] > 0]

        # Skip products with no valid prices
        if not all_prices:
            continue

        # Prefer lowest in-stock price, fall back to lowest overall if all OOS
        item["lowestPrice"] = min(in_stock_prices) if in_stock_prices else min(all_prices)
        item["inStock"] = any(v["inStock"] for v in item["vendors"])
        result.append(item)

    return result, fuzzy_matches


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
        print(f"Fetching with {MAX_WORKERS} parallel workers...")
    print()

    # Fetch or process all products in parallel
    all_products = []
    store_stats = []

    # Choose the processing function based on mode
    process_func = process_cached_products if args.offline else fetch_store_products

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all store fetches/processing
        future_to_store = {
            executor.submit(process_func, store): store
            for store in stores
        }

        # Collect results as they complete
        for future in as_completed(future_to_store):
            store = future_to_store[future]
            try:
                products, stats = future.result(timeout=FUTURE_TIMEOUT)
                all_products.extend(products)
                store_stats.append(stats)
            except TimeoutError:
                error_msg = f"Timeout after {FUTURE_TIMEOUT}s"
                safe_print(f"  Timeout fetching {store['name']} (exceeded {FUTURE_TIMEOUT}s)")
                store_stats.append(build_error_stats(
                    store["name"], store["url"], store.get("platform", "unknown"),
                    error_msg, duration=FUTURE_TIMEOUT
                ))
            except Exception as e:
                action = "processing" if args.offline else "fetching"
                safe_print(f"  Error {action} {store['name']}: {e}")
                store_stats.append(build_error_stats(
                    store["name"], store["url"], store.get("platform", "unknown"),
                    str(e)
                ))

    raw_count = len(all_products)
    total_fetched = sum(s["fetched"] for s in store_stats)

    # Consolidate duplicates across stores
    print()
    print("Consolidating products across stores...")
    all_products, fuzzy_matches = consolidate_products(all_products)
    print(f"  {raw_count} listings -> {len(all_products)} unique products")

    # Sort by lowest price
    all_products.sort(key=lambda p: p["lowestPrice"])

    scrape_duration = time.time() - scrape_start

    # Build output
    output = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "storeCount": len(stores),
        "productCount": len(all_products),
        "products": all_products,
    }

    # Calculate stock totals from unique products (not per-store sums)
    total_in_stock = count_in_stock(all_products)
    total_out_of_stock = len(all_products) - total_in_stock

    # Build stats output
    stats_output = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "duration": round(scrape_duration, 2),
        "stores": store_stats,
        "totals": {
            "rawProducts": total_fetched,
            "afterFilter": raw_count,
            "uniqueProducts": len(all_products),
            "fuzzyMatches": fuzzy_matches,
            "inStock": total_in_stock,
            "outOfStock": total_out_of_stock
        }
    }

    # Track price history
    print("\nTracking price changes...")
    history_data = load_history()
    price_stats = track_price_changes(all_products, history_data)
    current_product_ids = {p["id"] for p in all_products}
    cleanup_orphaned_products(history_data, current_product_ids)
    prune_old_entries(history_data)
    save_history(history_data)
    v = price_stats["vendors"]
    l = price_stats["lowest"]
    print(f"  Vendors: {v['new']} new, {v['changed']} changed, {v['unchanged']} unchanged")
    print(f"  Lowest:  {l['new']} new, {l['changed']} changed, {l['unchanged']} unchanged")

    # Add price history stats to stats output
    stats_output["priceHistory"] = price_stats

    # Write outputs
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    with open(STATS_FILE, "w") as f:
        json.dump(stats_output, f, indent=2)

    print()
    print("=" * 50)
    print(f"Done! Saved {len(all_products)} products to {OUTPUT_FILE}")
    print(f"Stats saved to {STATS_FILE}")
    print(f"Price history saved to {HISTORY_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    main()
