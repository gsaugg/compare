"""
Frontend data generator.

Transforms normalized data (items, matches, item-history) into
denormalized frontend files (products.json, tracker-data.json).

The frontend consumes the same format as before - this module
handles the conversion from our internal normalized structure.
"""

import json
import logging

from config import STORES_FILE, PROJECT_ROOT, MAX_TAGS

logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "public" / "data"
ITEMS_FILE = DATA_DIR / "items.json"
MATCHES_FILE = DATA_DIR / "matches.json"
PRODUCTS_FILE = DATA_DIR / "products.json"
TRACKER_DATA_FILE = DATA_DIR / "tracker-data.json"


def load_store_names() -> dict[str, str]:
    """Load store ID -> name mapping from stores.json."""
    with open(STORES_FILE) as f:
        data = json.load(f)

    return {s["id"]: s["name"] for s in data.get("stores", []) if "id" in s}


def generate_product(match: dict, items: dict, store_names: dict) -> dict | None:
    """Generate a single product entry from a match group.

    Args:
        match: Match group with 'id', 'matchedBy', 'items' keys
        items: Dict of all items
        store_names: Store ID -> name mapping

    Returns:
        Product dict in frontend format, or None if invalid
    """
    if not match.get("items"):
        return None

    # Get items in this match group
    match_items = []
    for item_id in match["items"]:
        item = items.get(item_id)
        if item:
            match_items.append(item)

    if not match_items:
        return None

    # Use first item as canonical source
    first_item = match_items[0]

    product = {
        "id": match["id"],
        "title": first_item["title"],
        "image": first_item.get("image"),
        "category": first_item.get("category", "Uncategorized"),
        "tags": list(first_item.get("tags", []))[:MAX_TAGS],
        "vendors": [],
    }

    # Build vendors list from all items
    seen_vendors = set()
    for item in match_items:
        store_id = item.get("storeId")
        store_name = store_names.get(store_id, store_id)

        # Skip duplicate vendors (shouldn't happen, but guard against it)
        if store_name in seen_vendors:
            continue
        seen_vendors.add(store_name)

        # Update product fields if better than current
        if product["image"] is None and item.get("image"):
            product["image"] = item["image"]

        if product["category"] == "Uncategorized" and item.get("category", "Uncategorized") != "Uncategorized":
            product["category"] = item["category"]

        # Merge tags
        product["tags"] = list(set(product["tags"] + item.get("tags", [])))[:MAX_TAGS]

        # Add vendor entry
        vendor = {
            "name": store_name,
            "price": item["price"],
            "regularPrice": item.get("regularPrice"),
            "url": item["url"],
            "inStock": item.get("inStock", True),
        }

        # Optional: include SKU for debugging
        if item.get("sku"):
            vendor["sku"] = item["sku"]

        product["vendors"].append(vendor)

    # Skip products with no vendors
    if not product["vendors"]:
        return None

    # Sort vendors: in-stock first, then by price
    product["vendors"].sort(key=lambda v: (not v["inStock"], v["price"]))

    # Calculate lowest price (prefer in-stock)
    all_prices = [v["price"] for v in product["vendors"] if v["price"] is not None and v["price"] > 0]
    in_stock_prices = [v["price"] for v in product["vendors"] if v["inStock"] and v["price"] is not None and v["price"] > 0]

    if not all_prices:
        return None

    product["lowestPrice"] = min(in_stock_prices) if in_stock_prices else min(all_prices)
    product["inStock"] = any(v["inStock"] for v in product["vendors"])

    return product


def generate_products(items: dict, matches: list, store_names: dict) -> list:
    """Generate products.json content from items and matches.

    Args:
        items: Dict of item_id -> item data
        matches: List of match groups
        store_names: Store ID -> name mapping

    Returns:
        List of products in frontend format
    """
    products = []
    for match in matches:
        product = generate_product(match, items, store_names)
        if product:
            products.append(product)

    # Sort by lowest price
    products.sort(key=lambda p: p["lowestPrice"])

    return products


def generate_tracker_data(item_history: dict, matches: list, items: dict, store_names: dict) -> dict:
    """Generate tracker-data.json from item history and matches.

    Transforms per-item history into per-product history with vendor breakdown.
    Includes price changes and stock transitions.

    Args:
        item_history: Dict with 'history' key containing per-item history
        matches: List of match groups
        items: Dict of item_id -> item data
        store_names: Store ID -> name mapping

    Returns:
        Tracker data dict in frontend format
    """
    history_entries = item_history.get("history", {})

    output = {
        "lastUpdated": item_history.get("lastUpdated"),
        "history": {},
    }

    for match in matches:
        match_id = match["id"]
        product_history = {
            "vendors": {},
            "lowest": [],
        }

        # Collect vendor histories for this match
        for item_id in match.get("items", []):
            item = items.get(item_id)
            if not item:
                continue

            store_id = item.get("storeId")
            store_name = store_names.get(store_id, store_id)
            item_entries = history_entries.get(item_id, [])

            if item_entries:
                # Convert to vendor history format with prev field for price changes
                # and stockPrev field for stock transitions
                vendor_history = []
                prev_price = None
                prev_stock = None
                for entry in item_entries:
                    vendor_entry = {"t": entry["t"], "p": entry["p"]}
                    # Include regular price if present (for detecting fake sales)
                    if "rp" in entry:
                        vendor_entry["rp"] = entry["rp"]
                    # Add prev field if price changed
                    if prev_price is not None and abs(entry["p"] - prev_price) >= 0.01:
                        vendor_entry["prev"] = prev_price
                    # Track stock transitions
                    current_stock = entry.get("s")
                    if current_stock is not None:
                        vendor_entry["s"] = current_stock
                        if prev_stock is not None and current_stock != prev_stock:
                            vendor_entry["stockPrev"] = prev_stock
                        prev_stock = current_stock
                    vendor_history.append(vendor_entry)
                    prev_price = entry["p"]

                product_history["vendors"][store_name] = vendor_history

        # Calculate consolidated lowest price history
        if product_history["vendors"]:
            # Merge all vendor histories by timestamp
            all_entries = []
            for vendor_name, entries in product_history["vendors"].items():
                for entry in entries:
                    all_entries.append({
                        "t": entry["t"],
                        "p": entry["p"],
                        "v": vendor_name,
                    })

            # Sort by time and build lowest history
            all_entries.sort(key=lambda e: e["t"])

            # For each unique timestamp, find the lowest price
            timestamps = sorted(set(e["t"] for e in all_entries))
            latest_prices = {}  # vendor -> latest price at each point
            prev_lowest = None  # Track previous lowest price

            for ts in timestamps:
                # Update latest prices with this timestamp's entries
                for entry in all_entries:
                    if entry["t"] == ts:
                        latest_prices[entry["v"]] = entry["p"]

                # Find lowest among current latest prices
                if latest_prices:
                    lowest = min(latest_prices.values())
                    lowest_vendor = min(latest_prices.items(), key=lambda x: x[1])[0]
                    entry = {
                        "t": ts,
                        "p": lowest,
                        "v": lowest_vendor,
                    }
                    # Add prev field if price changed
                    if prev_lowest is not None and abs(lowest - prev_lowest) >= 0.01:
                        entry["prev"] = prev_lowest
                    product_history["lowest"].append(entry)
                    prev_lowest = lowest

            output["history"][match_id] = product_history

    return output


def save_products(products: list, last_updated: str, store_count: int) -> None:
    """Save products.json."""
    output = {
        "lastUpdated": last_updated,
        "storeCount": store_count,
        "productCount": len(products),
        "products": products,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Saved {len(products)} products to {PRODUCTS_FILE}")


def save_tracker_data(tracker_data: dict) -> None:
    """Save tracker-data.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_DATA_FILE, "w") as f:
        json.dump(tracker_data, f, separators=(",", ":"))

    product_count = len(tracker_data.get("history", {}))
    logger.info(f"Saved tracker data for {product_count} products to {TRACKER_DATA_FILE}")


def generate_frontend_data(
    items: dict,
    matches: list,
    item_history: dict,
    last_updated: str,
    store_count: int,
) -> tuple[list, dict]:
    """Generate all frontend data files.

    Args:
        items: Dict of item_id -> item data
        matches: List of match groups
        item_history: Item-level history (price and stock)
        last_updated: ISO timestamp
        store_count: Number of enabled stores

    Returns:
        Tuple of (products list, tracker_data dict)
    """
    store_names = load_store_names()

    # Generate products
    products = generate_products(items, matches, store_names)

    # Generate tracker data (price and stock history)
    tracker_data = generate_tracker_data(item_history, matches, items, store_names)
    tracker_data["lastUpdated"] = last_updated

    # Save files
    save_products(products, last_updated, store_count)
    save_tracker_data(tracker_data)

    return products, tracker_data
