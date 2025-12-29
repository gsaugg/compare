"""
Product matching module.

Groups items by SKU (preferred) or fuzzy title matching.
Returns match groups with stable IDs for price history tracking.
"""

import hashlib
import logging
import re

from rapidfuzz import fuzz, process

from config import FUZZY_THRESHOLD

log = logging.getLogger(__name__)


def is_valid_sku(sku: str | None) -> bool:
    """Check if SKU is valid for matching.

    Valid SKUs are:
    - At least 4 characters
    - Contain at least one letter (excludes pure numeric IDs)
    - Alphanumeric with common separators (-, _)

    Examples:
        "AT-GLG-02" -> True (alphanumeric with letters)
        "WE-G17" -> True
        "12345" -> False (no letters)
        "AB" -> False (too short)
        "" -> False (empty)
    """
    if not sku or len(sku) < 4:
        return False

    # Must contain at least one letter
    if not re.search(r"[A-Za-z]", sku):
        return False

    return True


def normalize_title(title: str) -> str:
    """Normalize title for fuzzy matching.

    Strips colors, punctuation, normalizes whitespace.
    """
    title = title.lower().strip()
    # Remove common color suffixes
    title = re.sub(
        r"\s*[-–]\s*(black|tan|od|green|fde|grey|gray|white|red|blue|pink|orange|camo|multicam)\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    )
    # Remove punctuation except hyphens in product codes
    title = re.sub(r"[^\w\s-]", "", title)
    # Normalize whitespace
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def generate_title_id(title: str) -> str:
    """Generate a stable ID from title using hash.

    Uses first 8 chars of MD5 hash for reasonable uniqueness
    while keeping IDs short.
    """
    normalized = normalize_title(title)
    hash_str = hashlib.md5(normalized.encode()).hexdigest()[:8]
    return f"title-{hash_str}"


def match_items(items: dict) -> list[dict]:
    """Group items by SKU or fuzzy title matching.

    Args:
        items: Dict of item_id -> item data with keys:
            - title: Product title
            - sku: SKU (may be None or invalid)
            - storeId: Store identifier

    Returns:
        List of match groups:
        [
            {
                "id": "sku-AT-GLG-02" or "title-abc123",
                "matchedBy": "sku" or "title",
                "items": ["ceh|123|456", "gbu|789|012"]
            }
        ]

    Matching priority:
    1. SKU match (if valid alphanumeric SKU exists in group)
    2. Fuzzy title match (90% threshold)
    3. New group created if no match found
    """
    # SKU -> match group (for SKU-based matching)
    sku_groups: dict[str, dict] = {}

    # normalized_title -> match group (for title-based matching)
    title_groups: dict[str, dict] = {}

    # Track all matches for efficient lookup
    all_matches: list[dict] = []

    # Keys for fuzzy matching (normalized titles)
    title_keys: list[str] = []

    stats = {"sku_matches": 0, "fuzzy_matches": 0, "new_groups": 0}

    # Sort items for deterministic matching
    sorted_items = sorted(items.items(), key=lambda x: (normalize_title(x[1]["title"]), x[0]))

    for item_id, item in sorted_items:
        sku = item.get("sku")
        title = item.get("title", "")
        normalized = normalize_title(title)

        matched = False

        # 1. Try SKU match first (if item has valid SKU)
        if is_valid_sku(sku):
            sku_upper = sku.upper()  # Normalize SKU case
            if sku_upper in sku_groups:
                # Found SKU match
                sku_groups[sku_upper]["items"].append(item_id)
                stats["sku_matches"] += 1
                matched = True

        # 2. Try fuzzy title match (if no SKU match)
        if not matched and title_keys:
            result = process.extractOne(
                normalized, title_keys, scorer=fuzz.ratio, score_cutoff=FUZZY_THRESHOLD
            )
            if result:
                match_key = result[0]
                match_group = title_groups[match_key]
                match_group["items"].append(item_id)

                # Also register this item's SKU for future matches
                if is_valid_sku(sku):
                    sku_upper = sku.upper()
                    if sku_upper not in sku_groups:
                        sku_groups[sku_upper] = match_group
                        # Upgrade match type to SKU if it was title-based
                        if match_group["matchedBy"] == "title":
                            match_group["matchedBy"] = "sku"
                            match_group["id"] = f"sku-{sku_upper}"

                stats["fuzzy_matches"] += 1
                matched = True

        # 3. Create new group if no match found
        if not matched:
            if is_valid_sku(sku):
                sku_upper = sku.upper()
                match_id = f"sku-{sku_upper}"
                match_type = "sku"
            else:
                match_id = generate_title_id(title)
                match_type = "title"

            new_group = {"id": match_id, "matchedBy": match_type, "items": [item_id]}
            all_matches.append(new_group)

            # Register in appropriate lookup
            if is_valid_sku(sku):
                sku_groups[sku.upper()] = new_group

            title_groups[normalized] = new_group
            title_keys.append(normalized)

            stats["new_groups"] += 1

    log.info(
        f"Matching complete: {stats['new_groups']} groups, "
        f"{stats['sku_matches']} SKU matches, {stats['fuzzy_matches']} fuzzy matches"
    )

    return all_matches


def get_match_stats(matches: list[dict]) -> dict:
    """Get statistics about match groups.

    Returns:
        Dict with:
        - total_matches: Number of match groups
        - sku_matched: Groups matched by SKU
        - title_matched: Groups matched by title
        - multi_vendor: Groups with 2+ items (cross-store matches)
        - single_vendor: Groups with only 1 item
    """
    sku_matched = sum(1 for m in matches if m["matchedBy"] == "sku")
    title_matched = sum(1 for m in matches if m["matchedBy"] == "title")
    multi_vendor = sum(1 for m in matches if len(m["items"]) >= 2)
    single_vendor = sum(1 for m in matches if len(m["items"]) == 1)

    return {
        "total_matches": len(matches),
        "sku_matched": sku_matched,
        "title_matched": title_matched,
        "multi_vendor": multi_vendor,
        "single_vendor": single_vendor,
    }
