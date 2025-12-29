"""
Item-level price history tracking.

Simpler flat structure: one entry list per item_id.
Items are tracked at variant level with stable IDs.

Structure:
{
    "lastUpdated": "ISO timestamp",
    "history": {
        "ceh|123|456": [
            {"t": 1703880000, "p": 319.00},
            {"t": 1704052800, "p": 299.00, "rp": 350.00}
        ]
    }
}

Fields:
- t: timestamp
- p: price (current/sale price)
- rp: regular price (optional, only when on sale)

Each item_id is: storeId|productId|variantId
This uniquely identifies a specific variant at a specific store.
"""

import json
import logging
import time
from datetime import datetime, timezone

from config import HISTORY_RETENTION_DAYS, PROJECT_ROOT

logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "public" / "data"
ITEM_HISTORY_FILE = DATA_DIR / "item-history.json"


def load_history() -> dict:
    """Load existing item history from file."""
    if not ITEM_HISTORY_FILE.exists():
        logger.info("No existing item history file, starting fresh")
        return {"lastUpdated": None, "history": {}}

    try:
        with open(ITEM_HISTORY_FILE) as f:
            data = json.load(f)
            item_count = len(data.get("history", {}))
            logger.info(f"Loaded item history: {item_count} items tracked")
            return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Error loading item history, starting fresh: {e}")
        return {"lastUpdated": None, "history": {}}


def save_history(history_data: dict) -> None:
    """Save item history to file."""
    history_data["lastUpdated"] = datetime.now(timezone.utc).isoformat()

    ITEM_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(ITEM_HISTORY_FILE, "w") as f:
        json.dump(history_data, f, separators=(",", ":"))

    # Count total entries
    total_entries = sum(len(entries) for entries in history_data.get("history", {}).values())

    logger.info(
        f"Saved item history: {len(history_data['history'])} items, {total_entries} entries"
    )


def get_last_price(history_data: dict, item_id: str) -> float | None:
    """Get the most recent price for an item."""
    entries = history_data.get("history", {}).get(item_id)
    if not entries:
        return None

    # Return the last entry's price
    return entries[-1]["p"]


def record_price(
    history_data: dict, item_id: str, price: float, regular_price: float | None = None
) -> bool:
    """Record a price for an item if it changed.

    Args:
        history_data: The history data dict
        item_id: Item identifier (storeId|productId|variantId)
        price: Current price (sale price when on sale)
        regular_price: Regular/compare price (optional, only when on sale)

    Returns:
        True if a new entry was recorded (price or regular_price changed, or new item)
    """
    if "history" not in history_data:
        history_data["history"] = {}

    price = round(price, 2)
    rp = round(regular_price, 2) if regular_price else None
    now = int(time.time())

    entries = history_data["history"].get(item_id)

    if entries is None:
        # New item
        entry = {"t": now, "p": price}
        if rp:
            entry["rp"] = rp
        history_data["history"][item_id] = [entry]
        return True

    # Check if price or regular_price changed from last entry
    last = entries[-1]
    last_price = last["p"]
    last_rp = last.get("rp")

    price_changed = abs(price - last_price) >= 0.01
    # rp changed if: both exist and differ, or one exists and other doesn't
    rp_changed = (rp is not None and last_rp is not None and abs(rp - last_rp) >= 0.01) or (
        (rp is None) != (last_rp is None)
    )

    if price_changed or rp_changed:
        entry = {"t": now, "p": price}
        if rp:
            entry["rp"] = rp
        entries.append(entry)
        return True

    return False


def prune_old_entries(history_data: dict, days: int = HISTORY_RETENTION_DAYS) -> int:
    """Remove entries older than the retention period.

    Returns:
        Number of entries removed
    """
    cutoff = int(time.time()) - (days * 24 * 60 * 60)
    removed = 0

    for item_id in list(history_data.get("history", {}).keys()):
        entries = history_data["history"][item_id]
        original_count = len(entries)

        # Keep entries at or after cutoff
        history_data["history"][item_id] = [e for e in entries if e["t"] >= cutoff]
        removed += original_count - len(history_data["history"][item_id])

        # Remove item entirely if no entries left
        if not history_data["history"][item_id]:
            del history_data["history"][item_id]

    if removed > 0:
        logger.info(f"Pruned {removed} entries older than {days} days")

    return removed


def cleanup_orphaned_items(history_data: dict, current_item_ids: set[str]) -> int:
    """Remove history for items that no longer exist.

    Returns:
        Number of orphaned items removed
    """
    orphaned = [
        item_id
        for item_id in history_data.get("history", {}).keys()
        if item_id not in current_item_ids
    ]

    for item_id in orphaned:
        del history_data["history"][item_id]

    if orphaned:
        sample = orphaned[:5]
        logger.info(f"Cleaned up {len(orphaned)} orphaned items from history: {sample}")

    return len(orphaned)


def track_items(items: dict, history_data: dict) -> dict:
    """Track price changes for all items.

    Args:
        items: Dict of item_id -> item data (must have 'price' field, optionally 'regularPrice')
        history_data: The history data dict to update

    Returns:
        Stats dict with counts
    """
    stats = {"new": 0, "changed": 0, "unchanged": 0}

    for item_id, item in items.items():
        price = item.get("price")
        if price is None:
            continue

        regular_price = item.get("regularPrice")
        last_price = get_last_price(history_data, item_id)

        if last_price is None:
            record_price(history_data, item_id, price, regular_price)
            stats["new"] += 1
        elif record_price(history_data, item_id, price, regular_price):
            stats["changed"] += 1
        else:
            stats["unchanged"] += 1

    logger.info(
        f"Price tracking: {stats['new']} new, {stats['changed']} changed, "
        f"{stats['unchanged']} unchanged"
    )

    return stats
