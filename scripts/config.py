"""
Configuration constants for the GSAU.gg scraper.
"""

from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
STORES_FILE = PROJECT_ROOT / "stores.json"
OUTPUT_FILE = PROJECT_ROOT / "public" / "data" / "products.json"
STATS_FILE = PROJECT_ROOT / "public" / "data" / "stats.json"
HISTORY_FILE = PROJECT_ROOT / "public" / "data" / "price-history.json"
RAW_DATA_DIR = PROJECT_ROOT / ".cache" / "raw"  # Cache for offline mode

# Price history settings
HISTORY_RETENTION_DAYS = 30  # Keep price history for this many days

# Request settings
REQUEST_DELAY = 1.0  # seconds between requests (be respectful)
REQUEST_TIMEOUT = 30  # seconds
MAX_PAGES = 40  # max pages per store (safety limit)
MAX_WORKERS = 5  # parallel store fetches (don't set too high)
FUTURE_TIMEOUT = 300  # seconds to wait for each store fetch (5 min)

# Data quality
MIN_PRICE = 0.50  # Reject products under this price
FUZZY_THRESHOLD = 90  # Minimum similarity score for fuzzy matching (0-100)
MAX_TAGS = 10  # Maximum tags per product
MAX_ID_LENGTH = 50  # Maximum length for product IDs

# User agent for requests
USER_AGENT = "GSAU.gg/1.0 (+https://gsau.gg; gel blaster price comparison for Australian retailers)"
