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


def normalize_sku(sku: str) -> str:
    """Normalize SKU for matching.

    - Uppercase for case-insensitive matching
    - Strip parenthetical suffixes with leading space (e.g., "G296A (Short)" -> "G296A")

    Examples:
        "G296A (Short)" -> "G296A"
        "BYT-05T (TAN)" -> "BYT-05T"
        "M938-20 (NYLON)" -> "M938-20"
        "CAPA-01(BK)" -> "CAPA-01(BK)" (no space, kept as-is)
    """
    sku = sku.upper().strip()
    # Remove parenthetical suffix only if preceded by space
    sku = re.sub(r"\s+\([^)]+\)\s*$", "", sku)
    return sku


def normalize_title(title: str) -> str:
    """Normalize title for fuzzy matching.

    Removes punctuation (except hyphens), normalizes whitespace and case.
    Colors are preserved to ensure exact product matching.
    """
    title = title.lower().strip()
    # Remove punctuation except hyphens in product codes
    title = re.sub(r"[^\w\s-]", "", title)
    # Normalize whitespace
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def generate_title_id(title: str, use_raw: bool = False) -> str:
    """Generate a stable ID from title using hash.

    Uses first 8 chars of MD5 hash for reasonable uniqueness
    while keeping IDs short.

    Args:
        title: The product title
        use_raw: If True, use raw title instead of normalized (for unique IDs
                 when same-store items have similar normalized titles)
    """
    text = title.lower().strip() if use_raw else normalize_title(title)
    hash_str = hashlib.md5(text.encode()).hexdigest()[:8]
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

    # Track which stores are in each group (group_id -> set of store_ids)
    group_stores: dict[str, set] = {}

    # Track all matches for efficient lookup
    all_matches: list[dict] = []

    # Keys for fuzzy matching (normalized titles)
    title_keys: list[str] = []

    stats = {"sku_matches": 0, "fuzzy_matches": 0, "new_groups": 0, "same_store_skipped": 0}

    # Sort items for deterministic matching
    sorted_items = sorted(items.items(), key=lambda x: (normalize_title(x[1]["title"]), x[0]))

    for item_id, item in sorted_items:
        sku = item.get("sku")
        title = item.get("title", "")
        store_id = item.get("storeId")
        normalized = normalize_title(title)

        matched = False

        # 1. Try SKU match first (if item has valid SKU)
        if is_valid_sku(sku):
            sku_normalized = normalize_sku(sku)
            if sku_normalized in sku_groups:
                match_group = sku_groups[sku_normalized]
                # Only match if from a different store (cross-store matching only)
                if store_id not in group_stores.get(match_group["id"], set()):
                    match_group["items"].append(item_id)
                    group_stores[match_group["id"]].add(store_id)
                    stats["sku_matches"] += 1
                    matched = True
                else:
                    stats["same_store_skipped"] += 1

        # 2. Try fuzzy title match (if no SKU match)
        # Use token_sort_ratio to ignore word order differences
        if not matched and title_keys:
            result = process.extractOne(
                normalized, title_keys, scorer=fuzz.token_sort_ratio, score_cutoff=FUZZY_THRESHOLD
            )
            if result:
                match_key = result[0]
                match_group = title_groups[match_key]

                # Only match if from a different store (cross-store matching only)
                old_group_id = match_group["id"]
                if store_id not in group_stores.get(old_group_id, set()):
                    match_group["items"].append(item_id)
                    group_stores[old_group_id].add(store_id)

                    # Also register this item's SKU for future matches
                    if is_valid_sku(sku):
                        sku_normalized = normalize_sku(sku)
                        if sku_normalized not in sku_groups:
                            sku_groups[sku_normalized] = match_group
                            # Upgrade match type to SKU if it was title-based
                            if match_group["matchedBy"] == "title":
                                match_group["matchedBy"] = "sku"
                                new_group_id = f"sku-{sku_normalized}"
                                match_group["id"] = new_group_id
                                # Update group_stores with new ID
                                group_stores[new_group_id] = group_stores.pop(old_group_id)

                    stats["fuzzy_matches"] += 1
                    matched = True
                else:
                    stats["same_store_skipped"] += 1

        # 3. Create new group if no match found
        if not matched:
            if is_valid_sku(sku):
                sku_normalized = normalize_sku(sku)
                match_id = f"sku-{sku_normalized}"
                match_type = "sku"
            else:
                match_id = generate_title_id(title)
                # If ID already exists (same-store items with similar normalized titles),
                # use raw title to generate a unique ID
                if match_id in group_stores:
                    match_id = generate_title_id(title, use_raw=True)
                match_type = "title"

            # Ensure ID is unique by adding counter suffix if needed
            base_id = match_id
            counter = 1
            while match_id in group_stores:
                counter += 1
                match_id = f"{base_id}-{counter}"

            new_group = {"id": match_id, "matchedBy": match_type, "items": [item_id]}
            all_matches.append(new_group)

            # Track which stores are in this group
            group_stores[match_id] = {store_id}

            # Register in appropriate lookup
            if is_valid_sku(sku):
                sku_groups[sku_normalized] = new_group

            title_groups[normalized] = new_group
            title_keys.append(normalized)

            stats["new_groups"] += 1

    log.info(
        f"Matching complete: {stats['new_groups']} groups, "
        f"{stats['sku_matches']} SKU matches, {stats['fuzzy_matches']} fuzzy matches, "
        f"{stats['same_store_skipped']} same-store skipped"
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
