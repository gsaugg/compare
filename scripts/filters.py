"""
Product filtering rules for the GSAU.gg scraper.
Contains exclusion lists and filter functions.

Keywords are organized by category for easier maintenance.
Uses Aho-Corasick algorithm for efficient multi-pattern matching.
"""

from functools import lru_cache

import ahocorasick

# Keywords that indicate non-gel-blaster products, organized by category
EXCLUDED_TITLE_KEYWORDS_BY_CATEGORY = {
    "trading_cards": [
        "magic the gathering", "magic: the gathering", "mtg ", " mtg", "pokemon", "pokémon",
        "yu-gi-oh", "yugioh", "trading card", "booster", "tcg", "lorcana",
    ],
    "collectibles": [
        "funko", "pop vinyl", "anime figure", "marvel legends", "disney figure",
        "collectible figure", "vinyl figure", "action figure", "figurine",
        "bitty pop", "dragon shield", "ultra pro", "pop figure", "money box",
        "cosbaby", "bag clips", "nano vehicles", "walking dead", "mcfarlane",
    ],
    "general_toys": [
        "plush", "keychain", "card sleeve", "deck box", "card binder",
        "mystery box", "commander deck", "star wars socks", "r2d2 sock",
        "tonka", "bulldozer", "beyblade", "building set", "blind bag",
    ],
    "rc_parts_and_brands": [
        "du-bro", "dubro", "traxxas", "helion", "team magic", "dualsky",
        "g-force 0", "g-force 1", "g-force superflex",  # RC brand product codes
        "1/10 scale", "1/8 scale", "1/16 scale", "servo extension", "rc car", "rc plane",
        "oneway shim", "motor mount select", "body post select", "river hobby",
        "hpi ", " hpi", "slipper clutch", "battery post set", "remo hobby",
        "killerbody", "rc body", "rc bodies", "clear body",
        "wltoys", "udirc", "rc rock crawler", "1/24 2.4g", "1/22 electric",
        "1:22 electric", "brushless yellow",
        "hobbywing", "absima", "4wd rtr", "high speed truck",
        "rc tire glue", "hobby knife set", "servo horn", "servo saver",
    ],
    "rc_tanks": [
        "rc tank 2.4ghz", "rc tank 1/16", "sherman usa m4", "tiger i rc", "panzer rc",
        "heng long", "panther ausf", "rc tank 3879",
    ],
    "rc_construction": [
        "excavator digger", "tractor excavator", "tractor truck", "flatbed trailer",
        "huina", "actros",
    ],
    "model_kits": [
        "tamiya ts-", "tamiya 1/", "lacquer spray", "model kit",
        "finishing abrasive", "modeler's knife", "design knife", "italeri",
        "plastic model cement", "model cement", "zap pt-", "epoxy",
        "foam cure glue", "epp foam", "bob smith industries",
    ],
    "glue_supplies": [
        "zap-a-gap", "zap glue", "zap a gap", "rail-zip", "zap-a-dap", "flexible sealant",
    ],
    "star_wars_sabers": [
        "darth maul", "lightsaber", "battle saber", "saber blade", "youngling",
        "episode vii", "force awakens",
    ],
    "diecast_cars": [
        "1:24 scale", "road runner", "fast and furious",
    ],
    "knives": [
        "pocket knife", "folding knife", "olight heron",
        "chef's knife", "chef knife", "kitchen knife", "sheepdog knife",
    ],
    "puzzles_games": [
        "jigsaw puzzle", "chess set", "1000 piece",
        "catan", "soccer table", "football table", "table top game", "air soccer",
        "push rod soccer", "monopoly", "mousetrap", "top trumps", "uno ", " uno",
        "cluedo", "skip bo", "skipbo", "bop it", "scalextric",
    ],
    "cosplay_costumes": [
        "foam sword", "foam hammer", "battle hammer", "mjollnir", "thors hammer",
        "kratos blade", "blades of chaos",
        "baseball bat", "harley quinn bat", "lucille bat", "walking dead bat",
        "iron man mask", "cosplay helmet", "cyberpunk mask", "led mask",
        "cod headgear", "ghost mask cosplay",
        "cowboy holster", "cowboy belt", "old west holster", "western leather belt",
        "cowboy design",
    ],
    "wellness_furniture": [
        "massage roller", "muscle roller", "roller stick",
        "tripod stool", "folding stool",
    ],
    "dart_foam_blasters": [
        "foam dart blaster", "foam dart pistol", "soft dart blaster",
        "manual dart blaster", "dart blaster", "mini dart pistol",
        "nerf rival", "nerf dart", "nerf kronos", "nerf helios", "nerf gun",
    ],
    "laser_toys": [
        "laser pistol",
    ],
    "gun_safes": [
        "gun safe", "key safe", "gun key safe", "gun cabinet", "category a/b",
    ],
    "shipping_services": [
        "flat rate shipping", "shipping fee", "service fee", "postage fee",
    ],
    "standalone_lights": [
        "rear bike light", "bike light", "led lantern", "camping lantern",
        "keyring torch", "keychain torch", "pocket clip light", "clip light",
        "obulb", "olantern", "seemee", "gober clip",
    ],
    "fidget_toys": [
        "fidget spinner", "fidget toy", "karambit toy", "spin wheel toy",
    ],
    "anime_weapons": [
        "sandai kitetsu", "roronoa zoro sword",
    ],
    "quadcopters": [
        "quadcopter", "rc quadcopter",
    ],
    "warhammer": [
        "warhammer", "white dwarf", "age of sigmar",
        "stealth battlesuits", "blood master herald",
        "seraphon", "ossiarch", "lumineth", "soulblight",
    ],
    "clothing": [
        "father's day t-shirt", "dad t-shirt", "cotton t-shirt",
        "polyester cap", "military cap hat", "tactical t-shirt",
        "shirt childrens", "pants childrens", "childrens shorts",
        "childrens/kids caps",
    ],
    "misc": [
        "water bottle", "summer cat badge",
        "new moon", "twilight saga", "energy drink", "nootropic drink", "charged drink",
        "precision screwdriver set", "excel 55662",
        "top loaders", "card dividers", "inner sleeves", "ultimate guard",
        "card protector", "deck protector",
        "angus beef", "caramelised onion", "kettles",
        "retroarms sticker", "assorted sticker", "fridge magnet",
        "card holder", "pro hobbies",
    ],
}

# Flatten for use in filtering
EXCLUDED_TITLE_KEYWORDS = [
    keyword
    for keywords in EXCLUDED_TITLE_KEYWORDS_BY_CATEGORY.values()
    for keyword in keywords
]

# Tags that indicate non-gel-blaster products
EXCLUDED_TAGS_BY_CATEGORY = {
    "collectibles": [
        "rc parts", "pop funko", "funko pop", "pop figure", "pop vinyl", "pop!",
        "funko", "2nd hand", "money box", "pro hobbies",
    ],
    "model_kits": [
        "model kit", "model kits", "model kit plane",
        "italeri model kits", "italeri",
    ],
    "warhammer": [
        "warhammer", "warhammer40", "warhammer 40k", "games workshop", "citadel",
        "kill team", "space marines", "chaos space marines", "necrons",
        "xenos", "tau empire", "t'au empire", "astra militarum", "adepta sororitas",
        "armies of imperium", "armies of chaos", "army of xenos", "xenos armies",
        "warhammer single figure", "scenery", "citadel paint brush", "citadel accessories",
    ],
    "rc_vehicles": [
        "rc car", "rc plane", "rc flying", "crawler", "traxxas", "rc on road",
        "rc aircraft", "wheels/tyres", "crawler wheels/tyres", "rc accessories",
        "scale accessories", "traxxas spare parts",
    ],
    "games": [
        "boardgame", "board game", "card game", "slot car", "slot cars",
        "building blocks",
    ],
    "model_brands": [
        "airfix", "quickbuild", "quickbuild sets", "quickbuild cars",
    ],
    "diecast": [
        "fast & furious", "dice set",
    ],
}

# Flatten for use in filtering
EXCLUDED_TAGS = [
    tag
    for tags in EXCLUDED_TAGS_BY_CATEGORY.values()
    for tag in tags
]

# Categories that indicate non-gel-blaster products
EXCLUDED_CATEGORIES_BY_CATEGORY = {
    "trading_cards_games": [
        "magic the gathering", "pop vinyl", "collectible", "funko",
        "card game", "trading card", "rc car", "rc parts", "pop",
        "vinyl", "figure", "toy", "plush", "tcg", "lorcana",
        "card sleeve", "card binder", "deck box", "playmat", "chessex",
    ],
    "tabletop_gaming": [
        "warhammer", "dice", "dice set", "board game", "blood bowl",
        "d&d", "dungeons", "codex", "build kit",
    ],
    "hobby_supplies": [
        "paint", "paint brush", "hobby paint", "citadel", "spray paint",
        "fillers", "putties", "sand paper", "paint remover", "grease",
    ],
    "apparel_merch": [
        "shirt", "t-shirt", "hat", "pants", "shorts", "jacket",
        "singlet", "tank top", "uniform", "clothes", "clothing", "apparel",
        "patch", "sticker", "keyring", "keychain", "necklace", "bracelet",
        "memorabilia", "merch", "collectable",
    ],
    "toys_rc": [
        "nerf", "nerf gun", "water blaster", "water gun", "soft dart",
        "light saber", "lightsaber", "beyblade", "sword", "swords",
        "rc plane", "rc drone", "rc tank", "rc construction", "drone",
        "building blocks", "remote", "rc parts",
    ],
    "misc": [
        "money box", "tiki mug", "gift card", "party game", "model",
        "sports camera", "acrylic storage", "padlock", "monopoly", "monolpy",
        "wheels", "tires", "rc 4x4", "rc shell", "board", "labour", "services",
        "2nd hand", "custom shop", "mini blind bags", "tape", "knife",
        "energy drinks", "cosplay corner", "hobby and sport", "hobbies and sports",
        "camouflage netting", "laser pistols", "laser pistol",
    ],
}

# Flatten for use in filtering
EXCLUDED_CATEGORIES = [
    cat
    for cats in EXCLUDED_CATEGORIES_BY_CATEGORY.values()
    for cat in cats
]


# Build Aho-Corasick automata for efficient multi-pattern matching
def _build_automaton(keywords: list[str]) -> ahocorasick.Automaton:
    """Build an Aho-Corasick automaton from a list of keywords."""
    automaton = ahocorasick.Automaton()
    for keyword in keywords:
        automaton.add_word(keyword.lower(), keyword)
    automaton.make_automaton()
    return automaton


# Build automata at module load (one-time cost)
_title_automaton = _build_automaton(EXCLUDED_TITLE_KEYWORDS)
_tag_automaton = _build_automaton(EXCLUDED_TAGS)
_category_automaton = _build_automaton(EXCLUDED_CATEGORIES)


@lru_cache(maxsize=2048)
def is_excluded_by_title(title: str) -> bool:
    """Check if product title contains excluded keywords.

    Uses Aho-Corasick for O(n+m) matching instead of O(n*m).
    Results are cached for repeated titles.
    """
    title_lower = title.lower()
    for _ in _title_automaton.iter(title_lower):
        return True
    return False


def is_excluded_by_tags(tags: tuple) -> bool:
    """Check if product tags indicate it should be excluded.

    Uses Aho-Corasick for efficient pattern matching.
    Expects a tuple of tags for cache hashability.
    """
    for tag in tags:
        tag_lower = tag.lower().strip()
        for _ in _tag_automaton.iter(tag_lower):
            return True
    return False


@lru_cache(maxsize=1024)
def is_excluded_by_category(category: str) -> bool:
    """Check if product category indicates it should be excluded.

    Uses Aho-Corasick for O(n+m) matching.
    Results are cached for repeated categories.
    """
    if not category:
        return False
    cat_lower = category.lower()
    for _ in _category_automaton.iter(cat_lower):
        return True
    return False


# Reverse lookup: keyword -> category name
def _build_keyword_to_category_map(keywords_by_category: dict) -> dict:
    """Build a reverse lookup from keyword to its category name."""
    result = {}
    for category_name, keywords in keywords_by_category.items():
        for keyword in keywords:
            result[keyword.lower()] = category_name
    return result


_title_keyword_to_category = _build_keyword_to_category_map(EXCLUDED_TITLE_KEYWORDS_BY_CATEGORY)
_tag_keyword_to_category = _build_keyword_to_category_map(EXCLUDED_TAGS_BY_CATEGORY)
_category_keyword_to_category = _build_keyword_to_category_map(EXCLUDED_CATEGORIES_BY_CATEGORY)


def get_title_exclusion_match(title: str) -> tuple[str, str] | None:
    """Get the keyword and category that caused title exclusion.

    Returns (keyword, category) or None if not excluded.
    """
    title_lower = title.lower()
    for _, keyword in _title_automaton.iter(title_lower):
        category = _title_keyword_to_category.get(keyword.lower(), "unknown")
        return (keyword, category)
    return None


def get_tag_exclusion_match(tags: tuple) -> tuple[str, str] | None:
    """Get the keyword and category that caused tag exclusion.

    Returns (keyword, category) or None if not excluded.
    """
    for tag in tags:
        tag_lower = tag.lower().strip()
        for _, keyword in _tag_automaton.iter(tag_lower):
            category = _tag_keyword_to_category.get(keyword.lower(), "unknown")
            return (keyword, category)
    return None


def get_category_exclusion_match(category: str) -> tuple[str, str] | None:
    """Get the keyword and category that caused category exclusion.

    Returns (keyword, filter_category) or None if not excluded.
    """
    if not category:
        return None
    cat_lower = category.lower()
    for _, keyword in _category_automaton.iter(cat_lower):
        filter_category = _category_keyword_to_category.get(keyword.lower(), "unknown")
        return (keyword, filter_category)
    return None
