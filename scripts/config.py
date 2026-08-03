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
RAW_DATA_DIR = PROJECT_ROOT / ".cache" / "raw"  # Cache for offline mode

# Price history settings
HISTORY_RETENTION_DAYS = 365  # Keep price history for this many days

# Request settings
REQUEST_DELAY = 3.0  # seconds between requests (be respectful)
SHOPIFY_REQUEST_DELAY = 3.0  # longer delay for Shopify (shared rate limit across stores)
REQUEST_TIMEOUT = 30  # seconds
REQUEST_RETRIES = 5  # retry failed requests this many times
RETRY_DELAY = 5  # seconds to wait before retry
RATE_LIMIT_MAX_WAIT = 20  # cap the HTTP 429 Retry-After sleep at this many seconds
RATE_LIMIT_RETRIES = 3  # max 429 retries per page before giving up (then falls back to cache)
MAX_PAGES = 40  # max pages per store (safety limit)
MAX_WORKERS = 5  # parallel store fetches (don't set too high)
FUTURE_TIMEOUT = 300  # seconds to wait for each store fetch (5 min)

# Data quality
MIN_PRICE = 0.50  # Reject products under this price
FUZZY_THRESHOLD = 90  # Minimum similarity score for fuzzy matching (0-100)
FUZZY_THRESHOLD_MIXED = 95  # Higher threshold when mixing SKU and non-SKU items
MAX_TAGS = 10  # Maximum tags per product
MAX_ID_LENGTH = 50  # Maximum length for product IDs

# User agent for requests
USER_AGENT = "GSAU.gg/1.0 (+https://gsau.gg; gel blaster price comparison for Australian retailers)"
