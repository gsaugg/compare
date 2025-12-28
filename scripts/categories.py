"""
Category normalization and mapping for the GSAU.gg scraper.
Maps raw product categories to standardized categories.
"""

import re

# Category normalization - map messy categories to clean ones
CATEGORY_MAP = {
    # Blasters
    "gel blaster": "Blasters",
    "blaster": "Blasters",
    "stock blasters": "Blasters",
    "custom blasters": "Blasters",
    "blaster - rifle": "Rifles",
    "rifle": "Rifles",
    "rifles": "Rifles",
    "custom rifle": "Rifles",
    "gel blaster rifle": "Rifles",
    "ar series": "Rifles",
    "scar series": "Rifles",
    "hk416 series": "Rifles",
    "hk417": "Rifles",
    "ak series": "Rifles",
    "g36 series": "Rifles",
    "mcx series": "Rifles",
    "blaster - pistol": "Pistols",
    "pistol": "Pistols",
    "pistols": "Pistols",
    "custom pistol": "Pistols",
    "gel blaster pistol": "Pistols",
    "gas pistols": "Pistols",
    "gbb": "Pistols",
    "manual pistol": "Pistols",
    "electric pistol": "Pistols",
    "revolver": "Pistols",
    "1911 series": "Pistols",
    "g series": "Pistols",
    "hx series": "Pistols",
    "vx series": "Pistols",
    "smg": "SMGs",
    "smgs": "SMGs",
    "custom smg": "SMGs",
    "gel blaster smg": "SMGs",
    "mp5 series": "SMGs",
    "mp7 series": "SMGs",
    "ump series": "SMGs",
    "shotgun": "Shotguns",
    "shotguns": "Shotguns",
    "shot gun": "Shotguns",
    "blaster - shotgun": "Shotguns",
    "gel blaster shotgun": "Shotguns",
    "sniper": "Snipers",
    "snipers & dmr": "Snipers",
    "blaster - sniper": "Snipers",
    "lmg": "LMGs",
    "gel blaster light machine gun": "LMGs",

    # Parts - General
    "spare parts": "Parts",
    "parts (other)": "Parts",
    "internal parts": "Parts",
    "internals": "Parts",
    "internal": "Parts",
    "external upgrades": "Parts",
    "externals": "Parts",
    "external": "Parts",
    "replacement parts": "Parts",
    "upgrades": "Parts",
    "internal upgrades": "Parts",
    "retail parts": "Parts",

    # Parts - Specific
    "pistol parts": "Pistol Parts",
    "pistol parts & tools": "Pistol Parts",
    "gbbr parts": "GBBR Parts",
    "lmg parts": "LMG Parts",
    "hpa parts": "HPA Parts",
    "gearbox": "Gearboxes",
    "gearboxes": "Gearboxes",
    "gearbox parts": "Gearboxes",
    "spare parts - gearbox parts": "Gearboxes",
    "gears": "Gearboxes",
    "gear sets": "Gearboxes",
    "metal gears": "Gearboxes",
    "magazine": "Magazines",
    "magazines": "Magazines",
    "rifle magazine": "Magazines",
    "rifle mag": "Magazines",
    "pistol magazine": "Magazines",
    "pistol mag": "Magazines",
    "smg magazines": "Magazines",
    "lmg magazine": "Magazines",
    "spare parts - magazine": "Magazines",
    "magazine accessories": "Magazines",
    "hopup": "Hopups",
    "hop ups": "Hopups",
    "t-piece": "Hopups",
    "motor": "Motors",
    "motors": "Motors",
    "gel blaster motors": "Motors",
    "rifle motor": "Motors",
    "battery": "Batteries",
    "batteries": "Batteries",
    "7.4v batteries": "Batteries",
    "11.1v batteries": "Batteries",
    "charger": "Batteries",
    "battery charger": "Batteries",
    "spring": "Springs",
    "springs": "Springs",
    "trigger": "Triggers",
    "triggers": "Triggers",
    "piston": "Internals",
    "piston assembly": "Internals",
    "piston head": "Internals",
    "cylinder": "Internals",
    "cylinder head": "Internals",
    "tappet plate": "Internals",
    "nozzle": "Internals",
    "inner barrel": "Barrels",
    "inner barrels": "Barrels",
    "outer barrel": "Barrels",
    "outer barrels": "Barrels",
    "barrel": "Barrels",
    "stock": "Stocks",
    "stocks": "Stocks",
    "buttstock": "Stocks",
    "handguard": "Handguards",
    "handguards": "Handguards",
    "rifle handguard": "Handguards",
    "grips": "Grips",
    "grip": "Grips",
    "pistol grip": "Grips",
    "pistol grips": "Grips",
    "motor grip": "Grips",
    "foregrip": "Grips",
    "hand stop": "Grips",
    "receiver": "Receivers",
    "receivers": "Receivers",
    "rifle receiver": "Receivers",
    "lower receiver": "Receivers",

    # Accessories
    "accessories": "Accessories",
    "accessories,": "Accessories",
    "attachments": "Accessories",
    "tactical gear": "Tactical Gear",
    "tac gear": "Tactical Gear",
    "scope": "Optics",
    "scopes": "Optics",
    "scope/sight": "Optics",
    "sight": "Optics",
    "sights": "Optics",
    "red dot": "Optics",
    "magnifier": "Optics",
    "suppressor": "Muzzle Devices",
    "suppressors/flashhiders": "Muzzle Devices",
    "flash hider": "Muzzle Devices",
    "flash hider/suppressor": "Muzzle Devices",
    "flash suppressor": "Muzzle Devices",
    "tracer unit": "Muzzle Devices",
    "torch": "Lights & Lasers",
    "flashlight": "Lights & Lasers",
    "flashlights & lasers": "Lights & Lasers",
    "laser & torch": "Lights & Lasers",
    "holster": "Holsters & Bags",
    "bags/holsters/pouches": "Holsters & Bags",
    "pouch": "Holsters & Bags",
    "mag pouch": "Holsters & Bags",
    "sling": "Slings",
    "slings": "Slings",
    "rails": "Rails",
    "rails & riser": "Rails",
    "rail mount": "Rails",
    "bipod": "Bipods",
    "rifle bipod": "Bipods",
    "hpa": "HPA",
    "hpa engine": "HPA",
    "hpa adapter": "HPA",
    "gel balls": "Gel Balls",
    "gelballs": "Gel Balls",
    "gel ball": "Gel Balls",
    "gel ball ammunition": "Gel Balls",
    "gel blaster ammunition": "Gel Balls",
    "retail gels": "Gel Balls",
    "safety glasses": "Safety Gear",
    "goggles": "Safety Gear",
    "face mask": "Safety Gear",
    "mask": "Safety Gear",
    "gloves": "Safety Gear",
    "vest": "Tactical Gear",
    "tactical vest": "Tactical Gear",
    "chest rig": "Tactical Gear",
    "helmet": "Tactical Gear",
    "maintenance tool": "Tools",
    "hobby tool": "Tools",
    "tool kit": "Tools",
    "speed loader": "Accessories",
    "grenade": "Grenades",
    "grenades & claymores": "Grenades",
    "grenade launcher": "Grenades",
    "grenade & shell": "Grenades",
    # Brands used as categories -> Parts
    "cowcow": "Pistol Parts",
    "aps": "Parts",
    "lonex": "Parts",
    "dytac": "Parts",
    "classic army": "Parts",
    # Vague categories
    "general": "Accessories",
    "essentials": "Accessories",
    "consumables - pistol": "Pistol Parts",
    # Nested "Accessories - X" categories
    "accessories - sights": "Optics",
    "accessories - batteries and chargers": "Batteries",
    "accessories - holsters": "Holsters & Bags",
    "accessories - tracers": "Muzzle Devices",
    "accessories - case": "Holsters & Bags",
    "accessories - mounts": "Rails",
    # Price ranges -> ignore (map to Parts as fallback)
    "$500-$750": "Blasters",
    "$250-$500": "Blasters",
    "$750+": "Blasters",
    # Misc part mappings
    "spare parts - hpa": "HPA Parts",
    "blaster - upgraded": "Blasters",
    "blaster bags / cases": "Holsters & Bags",
    "blaster bag / cases": "Holsters & Bags",
    "aps shotgun / thor parts": "Parts",
    "other batteries & accessories": "Batteries",
    "green gas / co2 essentials": "Gas & CO2",
    "gas & co2": "Gas & CO2",
    "wiring & mosfets": "Electronics",
    "mosfet": "Electronics",
    "shims": "Internals",
    "o-rings": "Internals",
    "o-ring": "Internals",
    "orings": "Internals",
    "bushings & bearings": "Internals",
    "bushes": "Internals",
    "spring guide": "Springs",
    "spring set": "Springs",
    "spring kit": "Springs",
    "spring retainer": "Springs",
    "rifle spring": "Springs",
    "buffer tube": "Stocks",
    "buffer tubes": "Stocks",
    "cheek riser": "Stocks",
    "sight riser": "Optics",
    "scope mount": "Optics",
    "sight mount": "Optics",
    "balaclava": "Safety Gear",
    "target": "Accessories",
    "hydration pack": "Tactical Gear",
    "hydration pack tube": "Tactical Gear",
    "hydration": "Tactical Gear",
    "belt": "Tactical Gear",
    "belt loop": "Tactical Gear",
    "tactical belt": "Tactical Gear",
    "knee pad": "Tactical Gear",
    "elbow pad": "Tactical Gear",
    # HTML encoded categories
    "magazines &amp; drums": "Magazines",
    "east crane (e&amp;c)": "Parts",
    "bearing &amp; gears": "Internals",
    "rifles &amp; other blasters": "Blasters",
    "imperial custom &amp; precision": "Parts",
    "catelory a &amp; b an storage": "Holsters & Bags",
    "'hpa air fitting accessories": "HPA Parts",
    # Typos
    "accessoires": "Accessories",
    "helmat": "Tactical Gear",
    "nozzel": "Internals",
    # Vendor/marketing categories (fallback to title-based)
    "avada - best sellers": "",
    "best selling products": "",
    "new arrival": "",
    "new arrivals": "",
    "clearance": "",
    "boneyard clearance": "",
    "airtac customs": "Blasters",
    "gladiatair": "Parts",
    "cyber custom": "Parts",
    "essentials bundles": "",
    "blaster bundles": "Blasters",
    "technical support": "",
    "products": "",
    "sale": "",
    # Duplicate categories
    "gel blasters": "Blasters",
    "assault rifles": "Rifles",
    "gbb / pistols": "Pistols",
    "gas pistol": "Pistols",
    "eye protection": "Safety Gear",
    "gel": "Gel Balls",
    "gel ammo": "Gel Balls",
    "gels": "Gel Balls",
    "ammo": "Gel Balls",
    "sights / scopes": "Optics",
    "batteries and chargers": "Batteries",
    "barrels and outer barrels": "Barrels",
    "grips / bipods": "Grips",
    "handguards/ fishbones": "Handguards",
    "lubricants / gas": "Accessories",
    "flash light": "Lights & Lasers",
    "flash hiders": "Muzzle Devices",
    "silencers": "Muzzle Devices",
    "other parts": "Parts",
    "gel blaster parts": "Parts",
    "external parts": "Parts",
    "grenades / grenade launchers": "Grenades",
    "grenades and devices": "Grenades",
    "bags and backpacks": "Holsters & Bags",
    "hard case": "Holsters & Bags",
    "case": "Holsters & Bags",
    "pistol case": "Holsters & Bags",
    "bag": "Holsters & Bags",
    "holsters": "Holsters & Bags",
    "pouches": "Tactical Gear",
    "helmets": "Tactical Gear",
    "body protection": "Safety Gear",
    "face protection": "Safety Gear",
    "tactical safety glasses": "Safety Gear",
    "chargers": "Batteries",
    "bushes and bearings": "Internals",
    "mosfets": "Electronics",
    "accessories for gel blasters": "Accessories",
    "hpa accessories": "HPA Parts",
    "hpa regulator": "HPA",
    "regulator": "HPA",
    # Brand categories → Parts
    "ctm.tac part": "Pistol Parts",
    "gorilla": "Parts",
    "wolverine": "HPA",
    "eshooter": "Parts",
    "amped": "HPA",
    "ts-blades": "Accessories",
    "ar7 l.e.": "Parts",
    "40 max": "Parts",
    "aw": "Pistol Parts",
    "aw custom": "Pistol Parts",
    "rc": "Parts",
    "summer cat": "Parts",
    # Blaster model categories
    "ak series gel blaster": "Rifles",
    "m4/ar15": "Rifles",
    "ak": "Rifles",
    "ar9": "Rifles",
    "arp 9": "SMGs",
    "1911": "Pistols",
    "aap01 / rogb01": "Pistols",
    "hk416 gel blaster": "Rifles",
    "glock gel blaster": "Pistols",
    "golden eagle gel blaster": "Shotguns",
    "well gel blaster": "Blasters",
    "double bell gel blaster": "Blasters",
    "m1 garand": "Rifles",
    "ics lightway-peleador": "Rifles",
    "licensed 2011 series": "Pistols",
    "licensed dvc series": "Pistols",
    "peacemaker": "Pistols",
    "aeg": "Blasters",
    "gbbr": "GBBR Parts",
    "gbb part": "Pistol Parts",
    "part": "Parts",
    # Specific part categories
    "pistol slide": "Pistol Parts",
    "charging handles": "Parts",
    "rifle charging handle": "Parts",
    "rifle iron sight": "Optics",
    "pistol iron sight": "Optics",
    "pistol sight": "Optics",
    "pistol scope mount": "Optics",
    "gas rod assembly": "Pistol Parts",
    "gas internals": "Pistol Parts",
    "gas adaptor": "Pistol Parts",
    "gas blowback housing": "Pistol Parts",
    "pistol base plate": "Pistol Parts",
    "rifle base plate": "Parts",
    "pistol grip set": "Grips",
    "gbbr grip": "Grips",
    "mag well": "Pistol Parts",
    "magwell": "Pistol Parts",
    "pistol hammer": "Pistol Parts",
    "hammer set": "Pistol Parts",
    "pistol spring": "Pistol Parts",
    "pistol trigger": "Triggers",
    "rifle trigger": "Triggers",
    "trigger guard": "Parts",
    "bolt release": "Parts",
    "rifle mag release": "Parts",
    "anti-reverse latch": "Gearboxes",
    "reverse latch": "Gearboxes",
    "selector plate": "Gearboxes",
    "cut off lever": "Gearboxes",
    "trigger block": "Gearboxes",
    "cylinder assembly": "Gearboxes",
    "rifle gearbox": "Gearboxes",
    "gbbr m4 receiver parts": "GBBR Parts",
    "barrel parts": "Barrels",
    "barrel adapter": "Barrels",
    "barrel bushing & recoil spring plug": "Pistol Parts",
    "rifle t-piece": "Hopups",
    "gen 9 t-piece adaptor": "Hopups",
    "rifle outer barrel": "Barrels",
    "pistol barrel": "Barrels",
    "wire kit": "Electronics",
    "inline switch kit": "Electronics",
    "pinion": "Gearboxes",
    "o ring": "Internals",
    "slr parts": "Parts",
    "grip screws": "Parts",
    "motor base plate": "Motors",
    "recoil buffer": "Parts",
    "rocket valve": "Pistol Parts",
    "mag valve seal kits": "Magazines",
    "magazine parts": "Magazines",
    "mag coupler": "Magazines",
    "battery case": "Batteries",
    "pistol mat": "Accessories",
    "rifle maintenance mat": "Accessories",
    "targets": "Accessories",
    "lens": "Safety Gear",
    "mask lens": "Safety Gear",
    "mask foam kit": "Safety Gear",
    "laser": "Lights & Lasers",
    "light": "Lights & Lasers",
    "laser & torch switch": "Lights & Lasers",
    "pistol laser & torch": "Lights & Lasers",
    "drop leg mounts": "Tactical Gear",
    "mac accessories": "Parts",
    "pistol accessories": "Accessories",
    "giftcard": "",
    "launcher": "Grenades",
    "tank cover": "HPA",
    "adaptors": "Parts",
    "adaptor": "Parts",
    "adapter": "Parts",
    "rails & rails mount": "Rails",
    "plugs": "Parts",
    "multi-function tool": "Tools",
    "vernier caliper": "Tools",
    "pin punch set": "Tools",
    "electronic screw driver": "Tools",
    "silicone lubricant": "Accessories",
    "buttstocks/buffer tubes": "Stocks",
    "fuel": "Gas & CO2",
    "co2": "Gas & CO2",
    "gas": "Gas & CO2",
    "cabine conversion kit": "Parts",
    "gel blaster shooting training games": "Accessories",
    "14 inch": "Barrels",
    "manual operation": "Blasters",
    "gas gel blaster": "Pistols",
    "licensed blu series": "Pistols",
}

# Title-based categorization patterns (order matters - first match wins)
TITLE_CATEGORY_PATTERNS = [
    # Blasters - be specific to avoid false positives
    (r"\bgel blaster\b.*\brifle\b|\brifle\b.*\bgel blaster\b", "Rifles"),
    (r"\bgel blaster\b.*\bpistol\b|\bpistol\b.*\bgel blaster\b", "Pistols"),
    (r"\bgel blaster\b.*\bsmg\b|\bsmg\b.*\bgel blaster\b", "SMGs"),
    (r"\bgel blaster\b.*\bshotgun\b|\bshotgun\b.*\bgel blaster\b", "Shotguns"),
    (r"\bshotgun blaster\b|\brepeater shotgun\b", "Shotguns"),
    (r"\bgel blaster\b.*\bsniper\b|\bsniper\b.*\bgel blaster\b", "Snipers"),
    (r"\b(m4a1|m4|ar15|ar-15|hk416|scar|ak47|ak-47|g36|acr|mcx)\b.*(gel blaster|blaster)", "Rifles"),
    (r"\b(glock|1911|hi-?capa|hicapa|ppk|desert eagle|m9|m92|p226|sig|beretta)\b.*(gel blaster|blaster|pistol)", "Pistols"),
    (r"\b(mp5|mp7|ump|vector|p90|mac-?10|uzi)\b.*(gel blaster|blaster)", "SMGs"),
    (r"\belectric pistol\b|\bmanual pistol\b|\bgreen gas pistol\b", "Pistols"),
    (r"\bgas blowback\b|\bgbb\b.*\bpistol\b", "Pistols"),

    # Optics & lights
    (r"\bred dot\b|\breflex sight\b|\bholographic\b|\bacog\b|\bscope\b|\bsight riser\b", "Optics"),
    (r"\b(romeo5|aimpoint|eotech|holosun|bushnell|vortex)\b.*\b(sight|optic)\b", "Optics"),
    (r"\blaser sight\b|\bgreen laser\b|\bred laser\b", "Lights & Lasers"),

    # Suppressors & muzzle devices
    (r"\bsuppressor\b|\bsilencer\b", "Muzzle Devices"),
    (r"\bflash hider\b|\bmuzzle\s*(brake|break)\b|\bcompensator\b", "Muzzle Devices"),

    # Grips & foregrips
    (r"\bforegrip\b|\bfore\s*grip\b|\bvertical grip\b|\bangled grip\b", "Grips"),
    (r"\bpistol grip\b|\bmotor grip\b|\bhi-?capa grip\b|\bhicapa grip\b", "Grips"),

    # Pistol parts
    (r"\bhammer assembly\b|\bcocking handle\b|\bspeed cocking\b", "Pistol Parts"),
    (r"\bmag lips\b|\bfollower\b|\bslide\b.*\bhi-?capa\b", "Pistol Parts"),
    (r"\bhi-?capa\b.*\b(bundle|pro|kit)\b", "Pistols"),

    # Handguards & rails
    (r"\bhandguard\b|\bhand\s*guard\b|\bquad rail\b|\brail system\b|\bm-?lok\b|\bkeymod\b", "Handguards"),

    # Stocks
    (r"\bstock\b(?!.*\bin stock\b)|\bbuffer tube\b|\bbutt\s*stock\b", "Stocks"),

    # Magazines
    (r"\bmagazine\b|\bmag\b.*\b(spring|drum|extended)\b|\bdrum mag\b", "Magazines"),

    # Motors
    (r"\b(high torque|speed|aeg)\s*motor\b|\bmotor\b.*\b(chihai|shs|rocket)\b", "Motors"),

    # Batteries & chargers
    (r"\b\d+\.?\d*v\s*(battery|lipo)\b|\bbattery\b.*\bcharger\b|\blipo\b|\bnimh\b", "Batteries"),

    # Gearboxes
    (r"\bgearbox\b|\bgear\s*set\b|\bpiston\b|\bcylinder\b|\btappet\b|\bnozzle\b", "Gearboxes"),
    (r"\bmetal gears\b|\b14:1\s*gears\b|\b13:1\s*gears\b|\b18:1\s*gears\b", "Gearboxes"),

    # Hopups
    (r"\bhop\s*up\b|\bhopup\b|\bbucking\b|\bi-?key\b", "Hopups"),

    # Springs
    (r"\bspring\b.*\b(unequal|m\d+|fps)\b|\bunequal\b.*\bspring\b", "Springs"),

    # Barrels
    (r"\binner barrel\b|\bouter barrel\b|\btight bore\b|\b6\.0\d\s*mm\b.*\bbarrel\b", "Barrels"),

    # Tactical gear
    (r"\bplate carrier\b|\bchest rig\b|\btactical vest\b|\bmolle\b", "Tactical Gear"),
    (r"\bholster\b|\bsling\b|\bgun bag\b|\bblaster bag\b|\brifle bag\b", "Holsters & Bags"),
    (r"\bmag pouch\b|\bmagazine pouch\b|\bdump pouch\b|\butility pouch\b", "Tactical Gear"),
    (r"\brucksack\b|\bbackpack\b|\bmilitary bag\b", "Holsters & Bags"),

    # Accessories
    (r"\bchronograph\b|\bacetech\b", "Accessories"),
    (r"\btarget\s*set\b|\bshooting target\b", "Accessories"),

    # Safety gear
    (r"\bmask\b|\bgoggles\b|\beye protection\b|\bface protection\b|\bgloves\b", "Safety Gear"),

    # Gel balls
    (r"\bgel ball\b|\bgel\s*balls\b|\bhardened gel\b|\bmilkies\b|\bmilky\b", "Gel Balls"),

    # Rifles (more patterns)
    (r"\bak74u?\b|\baks?\s*\d+\b", "Rifles"),

    # More parts patterns
    (r"\bo\s*ring\b|\bseals?\b", "Internals"),
    (r"\bt[\s-]?piece\b", "Hopups"),
    (r"\bconnector\b|\badapter\b|\bwiring\b|\bplug\b", "Electronics"),
    (r"\btrigger\b", "Triggers"),
    (r"\bspring retainer\b|\breturn spring\b", "Springs"),
    (r"\bsticker\b|\bpatch\b|\bkey\s*ring\b", "Accessories"),
    (r"\bhelmet\b", "Tactical Gear"),
    (r"\bthread protector\b|\bthread saver\b", "Muzzle Devices"),
    (r"\bpin\b.*\bset\b|\bscrew\b.*\bkit\b|\bscrew\b.*\bset\b", "Parts"),
]

# Tag-based categorization (maps specific tags to categories)
TAG_CATEGORY_MAP = {
    # Blasters
    "gel blaster": "Blasters",
    "blasters": "Blasters",
    "custom blaster": "Blasters",
    "custom aeg": "Blasters",
    "unique customs": "Blasters",
    "bolt action": "Snipers",
    "bolt action rifles": "Snipers",
    "sniper": "Snipers",
    "shotgun": "Shotguns",
    "gas blowback": "Pistols",
    "gas blow back": "Pistols",
    "gasblowback": "Pistols",
    "gbb pistol": "Pistols",
    "hi capa": "Pistol Parts",
    "hicapa": "Pistol Parts",
    "cowcow": "Pistol Parts",
    "cow cow": "Pistol Parts",
    "guarder": "Pistol Parts",
    "magwell": "Pistol Parts",
    "mag well": "Pistol Parts",
    "gas parts": "Pistol Parts",
    "gas pistol maintenance": "Pistol Parts",
    "m4": "Rifles",
    "ak": "Rifles",
    "scar": "Rifles",
    # Parts
    "parts": "Parts",
    "gbu custom part": "Parts",
    "self build kit": "Parts",
    "internals": "Parts",
    "upgrades": "Parts",
    "modification": "Parts",
    # HPA
    "hpa parts": "HPA Parts",
    "polarstar": "HPA Parts",
    "polarstar parts": "HPA Parts",
    # Batteries
    "lipo battery": "Batteries",
    "batteries & chargers": "Batteries",
    "voltage": "Batteries",
    "charger": "Batteries",
    "charging": "Batteries",
    # Grenades
    "grenades": "Grenades",
    # Accessories
    "accessories": "Accessories",
    "grease kit": "Accessories",
    "lubricant": "Accessories",
}


def normalize_category(category: str) -> tuple[str, bool]:
    """
    Normalize a category name to a standard form.

    Returns:
        (category, was_suppressed): category name and whether it was explicitly suppressed
    """
    if not category:
        return "Uncategorized", False

    cat_lower = category.lower().strip()
    mapped = CATEGORY_MAP.get(cat_lower)

    # Empty string means "skip this category, use title-based"
    if mapped == "":
        return "Uncategorized", True

    return (mapped if mapped else category.title()), False


def categorize_by_title(title: str) -> str:
    """Try to categorize based on product title patterns."""
    title_lower = title.lower()
    for pattern, category in TITLE_CATEGORY_PATTERNS:
        if re.search(pattern, title_lower):
            return category
    return "Uncategorized"


def categorize_by_tags(tags: list) -> str:
    """Try to categorize based on product tags."""
    for tag in tags:
        tag_lower = tag.lower().strip()
        if tag_lower in TAG_CATEGORY_MAP:
            return TAG_CATEGORY_MAP[tag_lower]
    return "Uncategorized"


def get_best_category(raw_category: str, title: str, tags: list = None) -> str:
    """
    Determine the best category for a product using multiple strategies.

    Priority:
    1. Direct category mapping
    2. Title pattern matching
    3. Tag-based matching
    4. Fallback to original category or "Uncategorized"
    """
    if tags is None:
        tags = []

    # Try direct category mapping first
    category, was_suppressed = normalize_category(raw_category)
    if category != "Uncategorized" and category != raw_category.title():
        return category

    # Try title-based categorization
    title_category = categorize_by_title(title)
    if title_category != "Uncategorized":
        return title_category

    # Try tag-based categorization
    tag_category = categorize_by_tags(tags)
    if tag_category != "Uncategorized":
        return tag_category

    # If category was explicitly suppressed, stay Uncategorized
    if was_suppressed:
        return "Uncategorized"

    # Return the normalized original category or Uncategorized
    return category if category != "Uncategorized" else raw_category.title() if raw_category else "Uncategorized"
