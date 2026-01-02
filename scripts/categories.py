"""
Category normalization and mapping for the GSAU.gg scraper.
Maps raw product categories to standardized categories.
"""

import re

# Category normalization - map messy categories to clean ones
CATEGORY_MAP = {
    # Blasters - suppress generic ones to force title pattern detection
    # (allows parts with "Gel Blaster" category to be re-categorized by title)
    "gel blaster": "",
    "blaster": "",
    "stock blasters": "Blasters",
    "custom blasters": "Blasters",
    # Rifles - suppress generic ones to force title pattern detection
    "blaster - rifle": "",
    "rifle": "",
    "rifles": "",
    "custom rifle": "",
    "gel blaster rifle": "",
    # Keep specific series as they're usually accurate
    "ar series": "Rifles",
    "scar series": "Rifles",
    "hk416 series": "Rifles",
    "hk417": "Rifles",
    "ak series": "Rifles",
    "g36 series": "Rifles",
    "mcx series": "Rifles",
    # Pistols - suppress generic ones to force title pattern detection
    "blaster - pistol": "",
    "pistol": "",
    "pistols": "",
    "custom pistol": "",
    "gel blaster pistol": "",
    "gas pistols": "",
    "gbb": "",
    "manual pistol": "",
    "electric pistol": "",
    # Keep specific series as they're usually accurate
    "revolver": "Pistols",
    "1911 series": "Pistols",
    "g series": "Pistols",
    "hx series": "Pistols",
    "vx series": "Pistols",
    # SMGs - suppress generic
    "smg": "",
    "smgs": "",
    "custom smg": "",
    "gel blaster smg": "",
    # Keep specific series
    "mp5 series": "SMGs",
    "mp7 series": "SMGs",
    "ump series": "SMGs",
    # Shotguns - suppress generic
    "shotgun": "",
    "shotguns": "",
    "shot gun": "",
    "blaster - shotgun": "",
    "gel blaster shotgun": "",
    # Snipers
    "sniper": "",
    "snipers & dmr": "",
    "blaster - sniper": "",
    # LMGs
    "lmg": "",
    "gel blaster light machine gun": "",

    # Parts - General (suppress generic ones to force title pattern fallback)
    "spare parts": "",
    "parts (other)": "",
    "internal parts": "",
    "internals": "",
    "internal": "",
    "external upgrades": "",
    "externals": "",
    "external": "",
    "replacement parts": "",
    "upgrades": "",
    "internal upgrades": "",
    "retail parts": "",

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

    # Accessories - suppress generic to force title pattern detection
    "accessories": "",
    "accessories,": "",
    "attachments": "",
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
    "sling": "Attachments",
    "slings": "Attachments",
    "rails": "Attachments",
    "rails & riser": "Attachments",
    "rail mount": "Attachments",
    "bipod": "Attachments",
    "rifle bipod": "Attachments",
    "hpa": "HPA",
    "hpa engine": "HPA",
    "hpa adapter": "HPA",
    "gel balls": "Consumables",
    "gelballs": "Consumables",
    "gel ball": "Consumables",
    "gel ball ammunition": "Consumables",
    "gel blaster ammunition": "Consumables",
    "retail gels": "Consumables",
    "safety glasses": "Safety Gear",
    "goggles": "Safety Gear",
    "face mask": "Safety Gear",
    "mask": "Safety Gear",
    "gloves": "Safety Gear",
    "vest": "Tactical Gear",
    "tactical vest": "Tactical Gear",
    "chest rig": "Tactical Gear",
    "helmet": "Tactical Gear",
    "maintenance tool": "Accessories",
    "hobby tool": "Accessories",
    "tool kit": "Accessories",
    "speed loader": "Accessories",
    "grenade": "Grenades",
    "grenades & claymores": "Grenades",
    "grenade launcher": "Grenades",
    "grenade & shell": "Grenades",
    # Brands used as categories -> suppress to force title pattern detection
    # (these brands make both blasters AND parts, so title must determine)
    "cowcow": "Pistol Parts",
    "aps": "",
    "lonex": "",
    "dytac": "",
    "classic army": "",
    "aug": "Rifles",
    "cyma": "",
    "double bell": "",
    "golden eagle": "",
    "well": "",
    "src": "",
    "atomic": "",
    "king arms": "",
    "a&k": "",
    "sig": "Rifles",
    "steyr": "Rifles",
    "ar7": "Parts",
    "cap": "Tactical Gear",
    "custom build": "Blasters",
    "hammer spring": "Pistol Parts",
    "lucifer p4": "Pistol Parts",
    "licensed canik series": "Pistols",
    # More brands that mix blasters and parts
    "guarder": "",
    "nine ball": "",
    "dr black": "",
    "armourer works": "",
    "aw custom": "",
    "jg": "",
    "we tech": "",
    "tokyo marui": "",
    "army armament": "",
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
    "accessories - mounts": "Attachments",
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
    "green gas / co2 essentials": "Consumables",
    "gas & co2": "Consumables",
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
    "gel blasters": "",  # Suppress to force title pattern detection
    "assault rifles": "",  # Suppress to force title pattern detection
    "gbb / pistols": "Pistols",
    "gas pistol": "Pistols",
    "eye protection": "Safety Gear",
    "gel": "Consumables",
    "gel ammo": "Consumables",
    "gels": "Consumables",
    "ammo": "Consumables",
    "sights / scopes": "Optics",
    "batteries and chargers": "Batteries",
    "barrels and outer barrels": "Barrels",
    "grips / bipods": "Grips",
    "handguards/ fishbones": "Handguards",
    "lubricants / gas": "Accessories",
    "flash light": "Lights & Lasers",
    "flash hiders": "Muzzle Devices",
    "silencers": "Muzzle Devices",
    "other parts": "",
    "gel blaster parts": "",
    "external parts": "",
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
    "rails & rails mount": "Attachments",
    "plugs": "Parts",
    "multi-function tool": "Accessories",
    "vernier caliper": "Accessories",
    "pin punch set": "Accessories",
    "electronic screw driver": "Accessories",
    "silicone lubricant": "Accessories",
    "tools": "Accessories",
    "cleaning mat": "Accessories",
    "gun cleaning": "Accessories",
    "buttstocks/buffer tubes": "Stocks",
    "fuel": "Consumables",
    "co2": "Consumables",
    "gas": "Consumables",
    "cabine conversion kit": "Parts",
    "gel blaster shooting training games": "Accessories",
    "14 inch": "Barrels",
    "manual operation": "Blasters",
    "gas gel blaster": "Pistols",
    "licensed blu series": "Pistols",
}

# Title-based categorization patterns (order matters - first match wins)
TITLE_CATEGORY_PATTERNS = [
    # ========== PARTS DETECTION (must come FIRST to take precedence) ==========

    # Pistol parts - specific patterns (before blaster patterns)
    # Brand + parts keyword patterns
    (r"\b(guarder|nine ball|dr\.? black|cowcow|cow cow|jg|shs|we\s*tech|army armament)\b.*\b(slide|spring|valve|hammer|sear|piston|nozzle|barrel|mag|trigger|grip|guide)\b", "Pistol Parts"),
    (r"\b(gbb|gas blowback)\s*(pistol)?\b.*\b(mag|spring|valve|seal|trigger|hammer|slide|nozzle|barrel|grip|piston)\b", "Pistol Parts"),
    # Hi-Capa patterns (handle "hi capa", "hi-capa", "hicapa")
    (r"\b(hi[\s-]?capa|hicapa|1911|g17|g18|g19|g[\s-]?series|m92|p226|beretta|glock)\b.*\b(slide|spring|valve|hammer|sear|piston|nozzle|barrel|mag|trigger|grip|guide|recoil|leaf|knocker)\b", "Pistol Parts"),
    (r"\b(slide release|slide catch|slide lock|mag release|mag lips?|mag base|mag seal|mag follower|mag spring|mag valve)\b", "Pistol Parts"),
    (r"\b(hammer spring|recoil spring|leaf spring|valve spring|nozzle spring|sear spring|trigger bar)\b", "Pistol Parts"),
    # Input/output valve patterns (standalone, common in pistol parts)
    (r"\b(output valve|input valve|exhaust valve|gas route|air seal|piston lid)\b", "Pistol Parts"),
    # WELL brand patterns (common pistol parts manufacturer)
    (r"\bwell\b.*\b(valve|hammer|spring|sear|mag|slide|piston|nozzle|seal)\b", "Pistol Parts"),
    (r"\bwell\b.*\b(g55|1191|webley|revolver)\b.*\b(part|kit|valve|spring)\b", "Pistol Parts"),

    # Magazine detection - comprehensive patterns
    (r"\b(magazine|mag)\b.*\b(spring|terminal|coupler|base|lip|seal|follower|valve|nut|adapter)\b", "Magazines"),
    (r"\b(mag terminal|mag spring|mag coupler|mag base|mag seal|mag lips?)\b", "Magazines"),
    (r"\breplacement\s*(magazine|mag)\b|\b(magazine|mag)\s*replacement\b", "Magazines"),
    (r"\b(drum mag|stick mag|extended mag|mid.?cap|hi.?cap|low.?cap)\b", "Magazines"),
    (r"\b(m4|ak|mp5|vector|glock|1911|hi-?capa)\b.*\b(mag|magazine)\b", "Magazines"),
    (r"\bmagazine\b(?!.*\bpouch\b)", "Magazines"),  # magazine but not pouch

    # Gearbox/internal parts
    (r"\b(tappet plate|tappet return|selector plate|cut.?off lever|anti.?reverse|sector gear|spur gear|bevel gear)\b", "Gearboxes"),
    (r"\b(gearbox shell|gearbox case|gear set|metal gears?)\b", "Gearboxes"),
    (r"\b(piston head|piston assembly|cylinder head|cylinder set|nozzle head)\b", "Gearboxes"),

    # Motor parts
    (r"\bmotor\b.*\b(base|mount|plate|housing|cage|pinion|gear)\b", "Motors"),
    (r"\b(pinion gear|motor gear|motor pinion)\b", "Motors"),
    (r"\b(460|480|370)\s*(motor|short|long)\b", "Motors"),

    # Spring parts
    (r"\b(spring guide|spring retainer|spring set|spring kit|spring pack)\b", "Springs"),
    (r"\b(un-?equal|non-?linear)\b.*\bspring\b|\bspring\b.*\b(un-?equal|non-?linear)\b", "Springs"),
    (r"\bm\d{2,3}\s*spring\b|\bm\d{2,3}\b.*\b(aeg|gel blaster)\b.*\bspring\b", "Springs"),
    (r"\b(v2|v3)\s*spring\b|\bspring\s*(v2|v3)\b", "Springs"),

    # Barrel parts
    (r"\b(inner barrel|outer barrel|tight bore|precision barrel)\b", "Barrels"),
    (r"\b\d+\.?\d*\s*mm\s*(inner\s*)?barrel\b", "Barrels"),

    # Hopup parts
    (r"\b(hop.?up|hopup)\s*(unit|chamber|assembly|set)\b", "Hopups"),
    (r"\b(t-?piece|t piece)\s*(holder|adapter|set)?\b", "Hopups"),
    (r"\bbucking\b|\bi-?key\b", "Hopups"),

    # Stock parts
    (r"\b(buffer tube|stock tube|stock adapter)\b", "Stocks"),
    (r"\b(cheek riser|stock pad|butt pad)\b", "Stocks"),

    # Receiver parts
    (r"\b(receiver|body)\s*(set|kit|pin|screw)\b", "Receivers"),
    (r"\b(upper receiver|lower receiver)\b", "Receivers"),

    # Electronics
    (r"\b(mosfet|fcu|etu|electronic trigger)\b", "Electronics"),
    (r"\b(wiring kit|wire harness|silver wire|deans|tamiya|xt30|xt60)\s*(connector|plug|adaptor)?\b", "Electronics"),
    (r"\btrigger\s*switch\b|\b\d+\s*amp.*switch\b", "Electronics"),
    (r"\bmag\s*terminals?\b|\bv2\s*terminals?\b|\bterminals?\s*set\b", "Electronics"),

    # Generic parts patterns (catch remaining parts before blaster fallback)
    (r"\bnozzles?\b(?!.*\bhead\b)", "Internals"),  # nozzle/nozzles → Internals (but not nozzle head)
    (r"\bhammer\s*(group|kit|parts?|assembly)\b", "Pistol Parts"),
    (r"\b(parts?\s*kit|kit\s*parts?)\b", "Parts"),
    (r"\bgrip\s*(for|20mm|picatinny|rail)\b", "Grips"),  # grip for rail
    (r"\bgrip\b(?!.*\b(gel blaster|blaster|rifle|pistol|smg|shotgun)\b)", "Grips"),  # grip but not "grip gel blaster"

    # Parts with "gel blaster(s)" in title (must come before "gel blaster" fallback)
    (r"\bgel blasters?\b.*\b(cutoff|cut-?off)\s*switch\b|\b(cutoff|cut-?off)\s*switch\b.*\bgel blasters?\b", "Gearboxes"),
    (r"\bgel blasters?\b.*\bgears?\b|\bgears?\b.*\bgel blasters?\b", "Gearboxes"),
    (r"\bgel blasters?\b.*\bgear\s*box\b|\bgear\s*box\b.*\bgel blasters?\b", "Gearboxes"),
    (r"\bgel blasters?\b.*\bvalve\b|\bvalve\b.*\bgel blasters?\b", "Pistol Parts"),
    (r"\bgel blasters?\b.*\bgrip\b|\bgrip\b.*\bgel blasters?\b(?!.*\b(rifle|pistol|smg)\b)", "Grips"),
    (r"\bgel blasters?\b.*\bmagazines?\b|\bmagazines?\b.*\bgel blasters?\b", "Magazines"),

    # More motor patterns
    (r"\b(v2|v3)\s*motor\b|\bmotor\s*(v2|v3|short|long)\b", "Motors"),
    (r"\b(mp5|mp7|ak|m4)\b.*\bmotor\b", "Motors"),
    (r"\bupdated\s*motor\b|\bmotor\s*updated\b", "Motors"),

    # More bearing patterns
    (r"\b\d+\s*mm\s*bearings?\b|\bbearings?\s*\d+\s*mm\b", "Internals"),

    # Switch patterns
    (r"\bswitch\s*(block|assembly)\b", "Gearboxes"),

    # Magazine patterns (catch remaining)
    (r"\b(electric|ak|m4|mp5|g18|m92|double bell)\b.*\bmagazines?\b|\bmagazines?\b.*\b(electric|ak|m4|mp5)\b", "Magazines"),
    (r"\bmagazines\b", "Magazines"),  # plural magazines
    (r"\b(short|long|extended|drum)\s*magazine\b", "Magazines"),

    # Grenades
    (r"\b(smoke\s*)?grenade\b.*\bspring\b|\bspring\b.*\bgrenade\b", "Grenades"),

    # More specific parts with "gel blaster(s)" in title
    (r"\bgel blasters?\b.*\b(o-?ring|mag part)\b|\b(o-?ring|mag part)\b.*\bgel blasters?\b", "Internals"),
    (r"\bmag\s*release\b|\bmag\s*well\b", "Parts"),
    (r"\b(prometheus|laylax)\b.*\b(gear|spring|hop)\b", "Parts"),
    (r"\bhard\s*gear\b|\bgear\s*(set|high speed)\b", "Gearboxes"),

    # ========== BLASTER PATTERNS (come after parts detection) ==========

    # Blasters - be specific to avoid false positives
    (r"\bgel blasters?\b.*\brifle\b|\brifle\b.*\bgel blasters?\b", "Rifles"),
    (r"\bgel blasters?\b.*\bpistol\b|\bpistol\b.*\bgel blasters?\b", "Pistols"),
    (r"\bgel blasters?\b.*\bsmg\b|\bsmg\b.*\bgel blasters?\b", "SMGs"),
    (r"\bgel blasters?\b.*\bshotgun\b|\bshotgun\b.*\bgel blasters?\b", "Shotguns"),
    (r"\bshotgun blaster\b|\brepeater shotgun\b", "Shotguns"),
    (r"\bgel blasters?\b.*\bsniper\b|\bsniper\b.*\bgel blasters?\b", "Snipers"),
    (r"\b(m4a1|m4|ar15|ar-15|hk416|scar|ak47|ak-47|g36|acr|mcx)\b.*(gel blasters?|blasters?)", "Rifles"),
    (r"\b(glock|1911|hi-?capa|hicapa|ppk|desert eagle|m9|m92|p226|sig|beretta)\b.*(gel blasters?|blasters?|pistol)", "Pistols"),
    (r"\b(mp5|mp7|ump|vector|p90|mac-?10|uzi)\b.*(gel blasters?|blasters?)", "SMGs"),
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
    (r"\bgearbox\b|\bgear\s*set\b|\bpiston\b|\bcylinder\b|\btappet\b", "Gearboxes"),
    (r"\bmetal gears\b|\b14:1\s*gears\b|\b13:1\s*gears\b|\b18:1\s*gears\b", "Gearboxes"),

    # Hopups
    (r"\bhop\s*up\b|\bhopup\b|\bbucking\b|\bi-?key\b", "Hopups"),

    # Springs (including numbered springs like "1.3 Spring", "C-766")
    (r"\bspring\b.*\b(unequal|m\d+|fps)\b|\bunequal\b.*\bspring\b", "Springs"),
    (r"\b\d+\.?\d*\s*(mm\s*)?springs?\b|\bsprings?\s*c-?\d+\b", "Springs"),
    (r"\bpack\s*of\s*\d+\s*springs?\b", "Springs"),

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
    (r"\bgel ball\b|\bgel\s*balls\b|\bhardened gel\b|\bmilkies\b|\bmilky\b", "Consumables"),

    # Rifles (more patterns)
    (r"\bak74u?\b|\baks?\s*\d+\b", "Rifles"),

    # More parts patterns
    (r"\bo-?rings?\b|\bseals?\b", "Internals"),  # O-Ring, O Ring, ORing
    (r"\bt[\s-]?piece\b", "Hopups"),
    (r"\bconnector\b|\badapte?or\b|\bwiring\b|\bplug\b", "Electronics"),  # adapter/adaptor
    (r"\btrigger\b", "Triggers"),
    (r"\bspring retainer\b|\breturn spring\b|\bblow\s*back\s*spring\b", "Springs"),
    (r"\bsticker\b|\bpatch\b|\bkey\s*ring\b|\bgopro\b.*\bmount\b", "Accessories"),
    (r"\bhelmet\b", "Tactical Gear"),
    (r"\bthread protector\b|\bthread saver\b", "Muzzle Devices"),
    (r"\bpin\b.*\bset\b|\bscrew\b.*\bkit\b|\bscrew\b.*\bset\b", "Parts"),
    (r"\bdust cover\b|\brail cover\b", "Parts"),
    (r"\bface\s*mas[kt]\b|\bskull\s*mas[kt]\b", "Safety Gear"),
    (r"\bco2\b|\bcarbon dioxide\b|\bcartridge\b", "Consumables"),
    (r"\bdelay\s*chip\b|\blocking\s*plate\b", "Gearboxes"),
    (r"\bbolt\s*release\b|\bforward\s*assist\b", "Parts"),
    (r"\bbattery\s*(cover|latch|compartment|door)\b", "Parts"),
    (r"\bhopper\b.*\bmount\b|\bhopper\b", "Accessories"),
    (r"\bmotor\s*plugs?\b|\bmotor\s*wir(e|ing)\b", "Electronics"),
    (r"\bwasher\b|\bspacer\b", "Parts"),
    (r"\bgel\s*bottle\b", "Consumables"),
    (r"\balcohol\s*wipe\b|\bcleaning\s*wipe\b|\bcleaning\s*cloth\b|\bcleaning\s*mat\b|\bgun\s*cleaning\b", "Accessories"),
    (r"\bnozzle\s*(tip|head)\b|\brubber\s*nozzle\b|\bsilicone\s*nozzle\b", "Internals"),
    (r"\bpin\s*extractor\b|\bpunch\s*set\b", "Accessories"),
    (r"\bcutoff\s*switch\b|\bcut-?off\s*switch\b", "Gearboxes"),
    (r"\bmuzzle\s*adapt[eo]r\b|\bflash\s*hider\s*adapt[eo]r\b", "Muzzle Devices"),
    (r"\bsector\s*clip\b|\bgear\s*sector\b", "Gearboxes"),
    (r"\bmag\s*block\b|\bmagwell\s*block\b", "Parts"),
    (r"\bjst\b.*\b(wire|plug|adapt[eo]r)\b|\b(wire|plug)\b.*\bjst\b", "Electronics"),
    (r"\blipo\b.*\bbag\b|\bbattery\b.*\b(bag|safe)\b", "Batteries"),
    (r"\bgas\s*block\b(?!.*\bgas\s*block\s*rod\b)", "Parts"),  # gas block but not gas block rod
    (r"\bgas\s*block\s*rod\b", "Barrels"),  # gas block rod is barrel-related
    (r"\bbolt\s*catch\b", "Parts"),
    (r"\bmag\s*pull\b|\bmagazine\s*pull\b", "Magazines"),
    (r"\brail\s*set\b|\bpicatinny\s*(set|mount|rail)\b", "Attachments"),
    (r"\bsilver[\s-]?plated\s*wire\b|\bcopper\s*wire\b", "Electronics"),
    (r"\bmicroswitch\b|\bmicro\s*switch\b", "Electronics"),
    (r"\bface\s*cover\b|\bbandana\b|\bneck\s*gaiter\b|\bshemagh\b", "Safety Gear"),
    (r"\brecoil\s*plate\b|\bebb\s*recoil\b", "Gearboxes"),
    (r"\bweb\s*dominator\b|\bmolle\s*clip\b|\bgrimloc\b", "Tactical Gear"),
    (r"\bpinion\s*gear\b|\bmetal\s*pinion\b", "Gearboxes"),
    (r"\breplacement\s*switch\b", "Electronics"),
    (r"\bblack\s*out\s*kit\b|\bblackout\s*kit\b", "Parts"),

    # More specific patterns for uncategorized items
    (r"\balligator\s*clips?\b|\bcrocodile\s*clips?\b", "Electronics"),
    (r"\bmag\s*base\b|\bmagazine\s*base\b", "Magazines"),
    (r"\bwater\s*ammo\b|\bgel\s*ammo\b|\bghosts?\s*gels?\b|\bfrosty\s*gels?\b|\bultra\s*(elite|hard)\b", "Consumables"),
    (r"\bammo\s*\d+k?\s*pack\b|\b\d+k\s*pack\b|\bblue\s*force\s*ammo\b", "Consumables"),
    (r"\bfill\s*valve\b|\btank\s*fill\b|\brefill\b", "HPA"),
    (r"\biron\s*sights?\b|\bflip[\s-]?up\s*sights?\b|\bmbus\b|\brear\s*sight\b|\bfront\s*sight\b", "Optics"),
    (r"\bcastle\s*nut\b", "Parts"),
    (r"\bswitch\s*cover\b", "Parts"),
    (r"\bparacord\b|\b550\s*cord\b", "Tactical Gear"),
    (r"\bblowback\s*housing\b|\bblow\s*back\s*housing\b", "Pistol Parts"),
    (r"\bdump\s*bag\b|\bdump\s*pouch\b", "Holsters & Bags"),
    (r"\bhandle\s*covers?\b|\bgrip\s*covers?\b", "Grips"),
    (r"\bshotgun\s*shells?\b|\bshell\s*holder\b", "Grenades"),
    (r"\bknocker\b", "Pistol Parts"),
    (r"\banti[\s-]?rotation\b|\brotation\s*links?\b", "Parts"),
    (r"\bbearings?\s*\d+\s*mm\b|\b\d+\s*mm\s*bearings?\b|\bgeneric\s*bearings?\b", "Internals"),
    (r"\banti[\s-]?revers\w*\s*lever\b", "Gearboxes"),
    (r"\bmagnifier\s*sight\b|\bmagnifier\b", "Optics"),
    (r"\bsnap\s*ring\b.*\btool\b|\binstaller\s*tool\b", "Accessories"),
    (r"\bcamo\s*tape\b|\bwrap\s*roll\b|\bself\s*adhesive\b.*\btape\b", "Tactical Gear"),
    (r"\bprime\s*switch\b|\bmag\s*switch\b", "Electronics"),
    (r"\bshs\s*springs?\b|\bgenuine\s*.*springs?\b", "Springs"),
    (r"\bfire\s*selector\b|\bselector\s*set\b|\bambidextrous\b.*\bselector\b", "Parts"),
    (r"\bplunger\b|\brack\s*gear\b", "Gearboxes"),
    (r"\bmag\s*motor\b|\bmagazine\s*motor\b", "Magazines"),
    (r"\bfirst\s*aid\b", "Accessories"),
    (r"\blinear\s*amplifier\b", "Accessories"),

    # More uncategorized patterns (batch 2)
    (r"\bo\s*ring\b", "Internals"),  # "O ring" with space
    (r"\bblow\s*back\s*springs?\b", "Springs"),
    (r"\bgas\s*mag\s*base\b", "Magazines"),
    (r"\breplica\b.*\bsights?\b|\bplastic\s*sights?\b", "Optics"),
    (r"\bshot\s*gun\s*shells?\b", "Grenades"),  # "shot gun" with space
    (r"\bm\d{2,3}\s*springs?\b|\bm-?\d{2,3}\b.*\bsprings?\b|\bspring\s*upgrade\b", "Springs"),
    (r"\banti\s*reserve\b", "Gearboxes"),  # typo for "anti reverse"
    (r"\bgelball\s*barrel\b|\bstainless\s*steel\b.*\bbarrel\b", "Barrels"),
    (r"\beo\s*tech\b|\beotech\b|\breplica\b.*\bsight\b", "Optics"),
    (r"\banti[\s-]?fog\b", "Accessories"),
    (r"\bbalakl?ava\b", "Safety Gear"),  # balaclava/balaklava
    (r"\b45\s*degree\s*rail\b|\bside\s*rail\b|\boffset\s*rail\b", "Attachments"),
    (r"\bsteel\s*parts?\b|\bmetal\s*parts?\b", "Parts"),
    (r"\bhand\s*stop\b", "Grips"),
    (r"\brail\s*covers?\b", "Parts"),
    (r"\bpeq\b.*\bbox\b|\bbattery\s*box\b", "Batteries"),
    (r"\bcombat\s*knife\b|\brubber\s*knife\b|\btraining\s*knife\b", "Accessories"),
    (r"\b\d+\s*mm\s*bush(es|ings?)?\b|\bbush(es|ings?)?\s*\d+\s*mm\b|\blow\s*profile\s*bush", "Internals"),
    (r"\bmetal\s*targets?\b|\btargets?\s*\d+\s*pk\b", "Accessories"),
    (r"\bsniper\s*rifle\s*part\b", "Parts"),
    (r"\bselector\s*switch\b|\bswitch\s*lever\b", "Parts"),
    (r"\bmini\s*top\s*gas\b|\btop\s*gas\b|\bgreen\s*gas\b", "Consumables"),
    (r"\bsilicone\s*spray\b|\bgun\s*spray\b", "Accessories"),
    (r"\bretractable\s*buckle\b|\bbuckle\b", "Tactical Gear"),
    (r"\bgun\s*paint\b|\bbody\s*paint\b|\bcamo\s*paint\b|\bpuff\s*dino\b", "Accessories"),
    (r"\bwrench\b(?!.*\ballen\b)", "Accessories"),
    (r"\bm[\s-]?rated\s*springs?\b|\bfightingbro\b.*\bsprings?\b", "Springs"),
    (r"\bearpiece\b|\bheadset\b|\bwalkie\s*talkie\b|\bbaofeng\b", "Accessories"),
    (r"\bcharging\s*handle\b", "Parts"),
    (r"\balloy\s*(inner\s*)?barrels?\b", "Barrels"),
    (r"\badjustable\s*hop[\s-]?up\b", "Hopups"),
    (r"\bbearing\s*kit\b", "Internals"),
    (r"\bmagnet\b", "Accessories"),
    (r"\bwaldo\b.*\bpatch\b|\bcustom\s*patch\b", "Accessories"),

    # More uncategorized patterns (batch 3)
    (r"\balcohol\s*wipes?\b", "Accessories"),
    (r"\bblack[\s-]?out\s*kit\b", "Parts"),
    (r"\bm\s*series\b.*\bsprings?\b|\bsteel\s*springs?\b.*\bm\d+\b", "Springs"),
    (r"\bfire\s*mode\b", "Parts"),
    (r"\b(jingji|slr)\b.*\b(flash\s*hider|suppressor)\b", "Muzzle Devices"),
    (r"\b(jingji|slr)\b.*\bhand\s*stop\b", "Grips"),
    (r"\b(jingji|slr)\b.*\brail\s*covers?\b", "Parts"),
    (r"\brattler\s*plate\b|\bsig\s*rattler\b", "Parts"),
    (r"\bbearing\s*kits?\b", "Internals"),
    (r"\bnylon\s*sight\b.*\bset\b|\bsight\s*set\b", "Optics"),
    (r"\bhush\s*rings?\b|\bsilencer\s*rings?\b", "Parts"),
    (r"\bmagnetic\s*charger\b|\bcharger\s*cable\b", "Batteries"),
    (r"\brevolver\s*shells?\b", "Grenades"),
    (r"\boptic\s*mounts?\b", "Optics"),
    (r"\bhop[\s-]?up\s*barrel\b|\bbarrel\s*replacement\b", "Hopups"),
    (r"\bmod\s*rail\b|\bknights\s*armament\b", "Attachments"),
    (r"\bbrushed\s*motor\b|\bbrushless\s*motor\b|\b540\s*motor\b", "Motors"),
    (r"\bmode\s*selectors?\b", "Parts"),
    (r"\bstable\s*ring\b|\bring\s*mount\b", "Parts"),
    (r"\bnoveske\b.*\bsuppressor\b|\bpig\s*spitfire\b", "Muzzle Devices"),
    (r"\bpiano\s*steel\s*springs?\b|\bequal\s*springs?\b", "Springs"),
    (r"\bpolished\s*(inner\s*)?barrels?\b|\bblue\s*(polished\s*)?(inner\s*)?barrels?\b", "Barrels"),
    (r"\boriginal\s*mag\b|\btransparent\b.*\bmag\b", "Magazines"),
    (r"\bbearing\s*tool\b", "Accessories"),
    (r"\bswitch\s*covers?\b", "Parts"),
    (r"\bgas\s*mag\b", "Magazines"),  # broader gas mag pattern

    # More uncategorized patterns (batch 4)
    (r"\bresistance\s*switch\b", "Electronics"),
    (r"\bdouble\s*mag\s*clip\b|\bmag\s*clip\b|\bmag\s*coupler\b", "Magazines"),
    (r"\bmotor\s*replacement\b|\breplacement\s*motor\b|\bstandard\s*motor\b", "Motors"),
    (r"\bguarder\s*custom\s*parts?\b|\bguarder\b.*\bparts?\b", "Pistol Parts"),
    (r"\bbarrel\s*adapt[eo]r\b|\buniversal\s*barrel\b", "Barrels"),
    (r"\brail\s*kit\b", "Attachments"),
    (r"\bpin\s*connectors?\b|\bgold\s*pin\b", "Electronics"),
    (r"\bmetal\s*v\d\s*t[\s-]?piece\b|\bt[\s-]?piece\s*metal\b", "Hopups"),
    (r"\b\d\s*slot\s*rail\b|\bpicatinny\s*(height|riser)\b|\bqd\s*.*\brail\b", "Attachments"),
    (r"\bflash[\s-]?hider\b", "Muzzle Devices"),  # flash-hider with hyphen
    (r"\bmetal\s*cage\b|\bvg6\b", "Muzzle Devices"),
    (r"\bsilicone\s*lube\b|\blube\s*(medium|thicc|thin)\b", "Accessories"),

    # Grenades (including parts)
    (r"\bgrenade\b.*\b(pin|shell|part)\b|\bgrenade shell\b", "Grenades"),

    # Lubricants & maintenance
    (r"\blube\b|\blubricant\b|\bgrease\b|\bgun oil\b|\bsilicone oil\b|\bsuper lube\b", "Accessories"),

    # Spray paints (for blasters)
    (r"\b(gun|camo|blaster)\s*(paint|spray)\b", "Accessories"),
    (r"\baerosol\b.*\b(spray|primer)\b|\bspray primer\b", "Accessories"),

    # Targets
    (r"\btarget\b(?!\s*acquisition)", "Accessories"),

    # Gearbox parts not caught by current patterns
    (r"\banti[- ]?reverse\b|\breverse latch\b", "Gearboxes"),
    (r"\bsector\s*(gear|delay|chip)\b", "Gearboxes"),
    (r"\bshims?\b", "Internals"),  # shim or shims anywhere
    (r"\bpinion\s*gear\b", "Gearboxes"),
    (r"\bdetent\b", "Gearboxes"),  # anti-reverse detent
    (r"\bgears?\s*-\s*(shs|cnc|spiral|bevel|pinion|\d+:\d+)", "Gearboxes"),  # "Gears - SHS 12:1" format
    (r"\b(stainless\s*)?return\b.*\bspring\b|\bspring\b.*\b(stainless\s*)?return\b", "Springs"),  # return springs
    (r"\bbush(es|ings?)?\s*-\s*\d+\s*mm\b", "Internals"),  # "Bushes - 6mm" format

    # Pistol parts
    (r"\bmag\s*lips?\b", "Pistol Parts"),
    (r"\bknock(er)?\b.*\b(pistol|1911|hi-?capa|glock)\b", "Pistol Parts"),
    (r"\bexhaust valve\b|\bgas port\b", "Pistol Parts"),

    # Batteries
    (r"\bcr123\b|\brechargeable battery\b", "Batteries"),

    # Generic blaster detection (for items with marketing suffixes)
    (r"\b(gelstorm|cosmox)\b.*\bblaster\b", "Blasters"),
    (r"\bgbb\b.*\b(glock|beretta|m92|1911|p320|revolver|sig)\b", "Pistols"),
    (r"\bldt\b.*\b(hk416|m4|ak|scar)\b", "Rifles"),

    # More specific parts patterns
    (r"\breceiver\b", "Receivers"),
    (r"\bmotor\b.*\b(base|mount|plate|adjustable)\b|\b(480|460|370)\s*motor\b", "Motors"),
    (r"\bgbbr\b", "GBBR Parts"),
    (r"\bvalve\b.*\b(input|output|exhaust)\b", "Pistol Parts"),
    (r"\bbushings?\b", "Internals"),
    (r"\bnozzle\b(?!.*\bhead\b)", "Internals"),  # nozzle alone → Internals, nozzle head → Gearboxes
    (r"\bswitch\b.*\b(cutoff|cut-?off)\b", "Gearboxes"),  # cutoff switch → Gearboxes
    (r"\bsafety\b(?!.*\b(gear|glass|goggle))", "Parts"),
    (r"\bbase\s*plate\b", "Parts"),
    (r"\bblackout\s*kit\b|\bconversion\s*kit\b", "Parts"),

    # ========== FALLBACK BLASTER/CATEGORY DETECTION (must be LAST) ==========
    # These catch items when broad categories were suppressed

    # Rifles - specific model patterns
    (r"\b(m4a1|m4|ar15|ar-15|hk416|hk417|scar|ak47|ak-47|ak74|g36|acr|mcx|aug|m16|fal|g3|sr25|mk18)\b", "Rifles"),
    (r"\b(rifle|carbine)\b(?!.*\b(mag|spring|gear|motor|part|kit|grip|stock)\b)", "Rifles"),

    # Pistols - specific model patterns
    (r"\b(glock|g17|g18|g19|1911|hi-?capa|hicapa|m9|m92|p226|p320|ppk|usp|desert eagle|deagle|tt-?33|tokarev|beretta|sig sauer|walther|cz75|fnx)\b(?!.*\b(spring|valve|slide|barrel|nozzle|trigger|grip|mag|part)\b)", "Pistols"),
    (r"\b(pistol|handgun)\b(?!.*\b(mag|spring|gear|motor|part|kit|grip|slide|barrel|nozzle|valve)\b)", "Pistols"),

    # SMGs
    (r"\b(mp5|mp7|mp9|ump|ump45|vector|p90|mac-?10|uzi|pp-?19|ppsh|thompson|m3 grease)\b(?!.*\b(mag|spring|part)\b)", "SMGs"),
    (r"\bsmg\b(?!.*\b(mag|spring|gear|part)\b)", "SMGs"),

    # Shotguns
    (r"\b(m870|aa-?12|benelli|spas-?12|remington|mossberg|saiga)\b(?!.*\b(part|spring)\b)", "Shotguns"),
    (r"\bshotgun\b(?!.*\b(mag|spring|part)\b)", "Shotguns"),

    # Snipers
    (r"\b(vsr-?10|l96|m40|m24|kar98|ssg|awp|awm|svd|dragunov|m700|r700)\b(?!.*\b(part|spring)\b)", "Snipers"),
    (r"\b(sniper|bolt action|dmr)\b(?!.*\b(spring|part)\b)", "Snipers"),

    # LMGs
    (r"\b(m249|m60|rpk|pkm|mg42|stoner|lmg)\b(?!.*\b(part|spring|mag)\b)", "LMGs"),

    # Accessories fallback
    (r"\b(speed loader|chronograph|target|bb|tracer|flashlight|torch|laser)\b", "Accessories"),

    # Generic gel blaster fallback (very last)
    (r"\bgel blasters?\b", "Blasters"),
    (r"\bblasters?\b(?!.*\b(bag|case|pouch|storage))", "Blasters"),  # blaster(s) but not blaster bag/case
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
    "grenade parts": "Grenades",
    # Accessories
    "accessories": "Accessories",
    "grease kit": "Accessories",
    "lubricant": "Accessories",
    "oil": "Accessories",
    "spray paint": "Accessories",
    "target": "Accessories",
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

    Priority (most specific first):
    1. Title pattern matching - product name is most specific
    2. Tag-based matching - product tags are often accurate
    3. Direct category mapping - store categories (often too broad)
    4. Fallback to original category or "Uncategorized"
    """
    if tags is None:
        tags = []

    # Try title-based categorization first (most specific)
    title_category = categorize_by_title(title)
    if title_category != "Uncategorized":
        return title_category

    # Try tag-based categorization
    tag_category = categorize_by_tags(tags)
    if tag_category != "Uncategorized":
        return tag_category

    # Try direct category mapping (store categories)
    category, was_suppressed = normalize_category(raw_category)
    if category != "Uncategorized" and category != raw_category.title():
        return category

    # If category was explicitly suppressed, stay Uncategorized
    if was_suppressed:
        return "Uncategorized"

    # Return the normalized original category or Uncategorized
    return category if category != "Uncategorized" else raw_category.title() if raw_category else "Uncategorized"
