"""
Price history tracking for GSAU.gg.
Records price changes over time for trend analysis and charts.

Structure:
{
    "lastUpdated": "ISO timestamp",
    "history": {
        "product-id": {
            "vendors": {
                "Store Name": [{"t": timestamp, "p": price, "prev": prev_price}, ...]
            },
            "lowest": [{"t": timestamp, "p": price, "v": vendor}, ...]
        }
    }
}
"""

import json
import logging
import time
from pathlib import Path

from config import HISTORY_FILE, HISTORY_RETENTION_DAYS

logger = logging.getLogger(__name__)


def load_history() -> dict:
    """Load existing price history from file."""
    if not Path(HISTORY_FILE).exists():
        logger.info("No existing price history file, starting fresh")
        return {"lastUpdated": None, "history": {}}

    try:
        with open(HISTORY_FILE) as f:
            data = json.load(f)
            product_count = len(data.get("history", {}))
            logger.info(f"Loaded price history: {product_count} products tracked")
            return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Error loading price history, starting fresh: {e}")
        return {"lastUpdated": None, "history": {}}


def save_history(history_data: dict) -> None:
    """Save price history to file."""
    from datetime import datetime, timezone

    history_data["lastUpdated"] = datetime.now(timezone.utc).isoformat()

    Path(HISTORY_FILE).parent.mkdir(parents=True, exist_ok=True)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history_data, f, separators=(",", ":"))

    # Count total entries
    total_entries = 0
    for product in history_data.get("history", {}).values():
        for vendor_entries in product.get("vendors", {}).values():
            total_entries += len(vendor_entries)
        total_entries += len(product.get("lowest", []))

    logger.info(
        f"Saved price history: {len(history_data['history'])} products, {total_entries} entries"
    )


def get_last_vendor_price(history_data: dict, product_id: str, vendor: str) -> float | None:
    """Get the most recent price for a specific vendor of a product."""
    product = history_data.get("history", {}).get(product_id)
    if not product:
        return None

    vendor_entries = product.get("vendors", {}).get(vendor)
    if not vendor_entries:
        return None

    # Return the last entry's price
    return vendor_entries[-1]["p"]


def get_last_lowest_price(history_data: dict, product_id: str) -> float | None:
    """Get the most recent lowest price for a product."""
    product = history_data.get("history", {}).get(product_id)
    if not product:
        return None

    lowest_entries = product.get("lowest", [])
    if not lowest_entries:
        return None

    return lowest_entries[-1]["p"]


def _ensure_product_structure(history_data: dict, product_id: str) -> dict:
    """Ensure the product has the correct nested structure."""
    if "history" not in history_data:
        history_data["history"] = {}

    if product_id not in history_data["history"]:
        history_data["history"][product_id] = {"vendors": {}, "lowest": []}

    product = history_data["history"][product_id]
    if "vendors" not in product:
        product["vendors"] = {}
    if "lowest" not in product:
        product["lowest"] = []

    return product


def record_vendor_price_change(
    history_data: dict,
    product_id: str,
    vendor: str,
    price: float,
    prev_price: float | None,
) -> None:
    """Record a price change for a specific vendor."""
    product = _ensure_product_structure(history_data, product_id)

    if vendor not in product["vendors"]:
        product["vendors"][vendor] = []

    entry = {
        "t": int(time.time()),
        "p": round(price, 2),
    }

    if prev_price is not None and abs(prev_price - price) >= 0.01:
        entry["prev"] = round(prev_price, 2)

    product["vendors"][vendor].append(entry)


def record_lowest_price_change(
    history_data: dict,
    product_id: str,
    price: float,
    vendor: str,
    prev_price: float | None,
) -> None:
    """Record a change in the lowest price for a product."""
    product = _ensure_product_structure(history_data, product_id)

    entry = {
        "t": int(time.time()),
        "p": round(price, 2),
        "v": vendor,
    }

    if prev_price is not None and abs(prev_price - price) >= 0.01:
        entry["prev"] = round(prev_price, 2)

    product["lowest"].append(entry)


def prune_old_entries(history_data: dict, days: int = HISTORY_RETENTION_DAYS) -> int:
    """Remove entries older than the retention period."""
    cutoff = int(time.time()) - (days * 24 * 60 * 60)
    removed = 0

    for product_id in list(history_data.get("history", {}).keys()):
        product = history_data["history"][product_id]

        # Prune vendor entries
        for vendor in list(product.get("vendors", {}).keys()):
            entries = product["vendors"][vendor]
            original_count = len(entries)
            product["vendors"][vendor] = [e for e in entries if e["t"] >= cutoff]
            removed += original_count - len(product["vendors"][vendor])

            # Remove vendor if no entries left
            if not product["vendors"][vendor]:
                del product["vendors"][vendor]

        # Prune lowest entries
        lowest = product.get("lowest", [])
        original_count = len(lowest)
        product["lowest"] = [e for e in lowest if e["t"] >= cutoff]
        removed += original_count - len(product["lowest"])

        # Remove product entirely if empty
        if not product.get("vendors") and not product.get("lowest"):
            del history_data["history"][product_id]

    if removed > 0:
        logger.info(f"Pruned {removed} entries older than {days} days")

    return removed


def cleanup_orphaned_products(history_data: dict, current_product_ids: set[str]) -> int:
    """Remove history for products that no longer exist."""
    orphaned = [
        pid
        for pid in history_data.get("history", {}).keys()
        if pid not in current_product_ids
    ]

    for pid in orphaned:
        del history_data["history"][pid]

    if orphaned:
        logger.info(f"Cleaned up {len(orphaned)} orphaned products from history")

    return len(orphaned)


def track_price_changes(products: list[dict], history_data: dict) -> dict:
    """Track price changes for all products.

    Tracks both per-vendor prices and consolidated lowest price.

    Returns: Stats dict with counts
    """
    stats = {
        "vendors": {"new": 0, "changed": 0, "unchanged": 0},
        "lowest": {"new": 0, "changed": 0, "unchanged": 0},
    }

    for product in products:
        product_id = product["id"]

        # Track per-vendor prices
        for vendor in product.get("vendors", []):
            vendor_name = vendor["name"]
            current_price = vendor["price"]
            prev_price = get_last_vendor_price(history_data, product_id, vendor_name)

            if prev_price is None:
                record_vendor_price_change(
                    history_data, product_id, vendor_name, current_price, None
                )
                stats["vendors"]["new"] += 1
            elif abs(current_price - prev_price) >= 0.01:
                record_vendor_price_change(
                    history_data, product_id, vendor_name, current_price, prev_price
                )
                stats["vendors"]["changed"] += 1
            else:
                stats["vendors"]["unchanged"] += 1

        # Track consolidated lowest price
        lowest_price = product.get("lowestPrice")
        if lowest_price is not None and product.get("vendors"):
            # Find which vendor has the lowest price
            lowest_vendor = min(product["vendors"], key=lambda v: v["price"])
            prev_lowest = get_last_lowest_price(history_data, product_id)

            if prev_lowest is None:
                record_lowest_price_change(
                    history_data, product_id, lowest_price, lowest_vendor["name"], None
                )
                stats["lowest"]["new"] += 1
            elif abs(lowest_price - prev_lowest) >= 0.01:
                record_lowest_price_change(
                    history_data, product_id, lowest_price, lowest_vendor["name"], prev_lowest
                )
                stats["lowest"]["changed"] += 1
            else:
                stats["lowest"]["unchanged"] += 1

    return stats
