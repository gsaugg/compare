"""
Base fetcher class for e-commerce platforms.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import requests

from config import (
    REQUEST_DELAY,
    REQUEST_TIMEOUT,
    REQUEST_RETRIES,
    RETRY_DELAY,
    RATE_LIMIT_MAX_WAIT,
    RATE_LIMIT_RETRIES,
    USER_AGENT,
    MAX_PAGES,
)
from utils import count_in_stock

logger = logging.getLogger(__name__)


class StoreLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that prefixes messages with store name."""

    def process(self, msg, kwargs):
        return f"{self.extra['store']}: {msg}", kwargs


class BaseFetcher(ABC):
    """Abstract base class for store fetchers.

    Uses template method pattern for fetch(). Subclasses implement:
    - platform_name: Platform identifier
    - _build_page_url(page): URL for a page
    - _extract_products(data): Extract product list from response
    - _is_last_page(data, page): Check if this is the last page
    - _parse_products(products): Parse/filter products (optional override)
    """

    def __init__(self, store_name: str, base_url: str):
        self.store_name = store_name
        self.base_url = base_url.rstrip('/')
        self.products = []
        self.error = None
        self.start_time = None
        self.duration = 0
        self.total_fetched = 0
        self.total_filtered = 0
        # Logger with store name prefix
        self.log = StoreLoggerAdapter(logger, {'store': store_name})

    @property
    def headers(self) -> dict:
        """Default headers for requests."""
        return {"User-Agent": USER_AGENT}

    def _make_request(self, url: str, timeout: int = REQUEST_TIMEOUT) -> requests.Response:
        """Make an HTTP request with standard error handling."""
        return requests.get(url, timeout=timeout, headers=self.headers)

    def _delay(self) -> None:
        """Delay between requests to be respectful."""
        time.sleep(REQUEST_DELAY)

    def fetch(self) -> tuple[list, dict]:
        """
        Fetch all products from the store (template method).

        Subclasses customize via:
        - _build_page_url(page): Build URL for each page
        - _extract_products(data): Extract products from response
        - _is_last_page(data, page): Check if pagination is complete
        - _rate_limit_wait(response): Capped wait (s) when rate limited (optional)
        - _parse_response(response): Parse response to JSON (optional)

        Returns:
            tuple: (list of products, stats dict)
        """
        self.products = []
        self.total_fetched = 0
        self.total_filtered = 0
        page = 1
        self.start_time = time.time()

        self.log.info("Fetching...")

        # Setup hook for subclasses (e.g., WooCommerce API detection)
        self._setup()

        while page <= MAX_PAGES:
            url = self._build_page_url(page)

            # Retry loop for network failures. Rate-limit (429) waits are
            # capped and counted separately, so they don't multiply against
            # the network-retry budget the way an unbounded Retry-After would.
            data = None
            last_error = None
            rate_limit_hits = 0
            attempt = 0
            while attempt <= REQUEST_RETRIES:
                try:
                    response = self._make_request(url)

                    # Handle rate limiting (429) with a capped, bounded wait.
                    wait = self._rate_limit_wait(response)
                    if wait is not None:
                        rate_limit_hits += 1
                        if rate_limit_hits > RATE_LIMIT_RETRIES:
                            last_error = requests.HTTPError(
                                f"still rate limited (429) after {RATE_LIMIT_RETRIES} retries"
                            )
                            self.log.error(f"Page {page}: {last_error}, giving up (will try cache)")
                            break
                        self.log.warning(
                            f"Page {page}: rate limited, waiting {wait}s "
                            f"(retry {rate_limit_hits}/{RATE_LIMIT_RETRIES})..."
                        )
                        time.sleep(wait)
                        continue  # retry same page without consuming the network-retry budget

                    response.raise_for_status()
                    data = self._parse_response(response)
                    break  # Success, exit retry loop

                except requests.RequestException as e:
                    last_error = e
                    attempt += 1
                    if attempt <= REQUEST_RETRIES:
                        self.log.warning(f"Page {page} failed (attempt {attempt}), retrying in {RETRY_DELAY}s...")
                        time.sleep(RETRY_DELAY)
                    else:
                        self.log.error(f"Page {page} failed after {REQUEST_RETRIES + 1} attempts: {e}")
                except json.JSONDecodeError as e:
                    last_error = e
                    self.log.error(f"JSON parse error: {e}")
                    break  # Don't retry JSON errors

            # If all retries failed, record error and stop
            if data is None:
                if last_error:
                    self.error = str(last_error)
                break

            page_products = self._extract_products(data)
            if not page_products:
                break

            self.total_fetched += len(page_products)
            raw_products, filtered_count = self._parse_products(page_products)
            self.products.extend(raw_products)
            self.total_filtered += filtered_count

            self._log_page_progress(page, len(page_products))

            if self._is_last_page(data, page, page_products):
                break

            page += 1
            self._delay()

        return self._finalize()

    def _setup(self) -> None:
        """Optional setup hook called before pagination starts."""
        pass

    @abstractmethod
    def _build_page_url(self, page: int) -> str:
        """Build URL for the given page number."""
        pass

    @abstractmethod
    def _extract_products(self, data: Any) -> list:
        """Extract product list from API response data."""
        pass

    def _is_last_page(self, data: Any, page: int, products: list) -> bool:
        """Check if this is the last page. Override for custom logic."""
        return False  # Default: continue until empty response

    def _rate_limit_wait(self, response: requests.Response) -> int | None:
        """Return capped seconds to wait when rate limited, or None if not.

        Default handling covers HTTP 429 for any platform: honor the server's
        ``Retry-After`` header when present, but cap it at ``RATE_LIMIT_MAX_WAIT``
        so a large value can't stall the run. Override for platform-specific
        rate-limit signals.
        """
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "")
            wait = int(retry_after) if retry_after.isdigit() else RETRY_DELAY
            return min(wait, RATE_LIMIT_MAX_WAIT)
        return None

    def _parse_response(self, response: requests.Response) -> Any:
        """Parse response to JSON. Override for custom parsing."""
        return response.json()

    def _parse_products(self, products: list) -> tuple[list, int]:
        """Parse raw products. Override if filtering is needed."""
        return products, 0

    def _log_page_progress(self, page: int, count: int) -> None:
        """Log progress. Override for custom format."""
        self.log.info(f"Page {page}: {count} products")

    def _finalize(self) -> tuple[list, dict]:
        """Finalize fetch and return results."""
        self.duration = time.time() - self.start_time
        in_stock = count_in_stock(self.products)
        self.log.info(f"Done: {len(self.products)} products fetched")

        stats = self.build_stats(
            fetched=self.total_fetched,
            filtered=self.total_filtered,
            final=len(self.products),
            in_stock=in_stock,
            out_of_stock=len(self.products) - in_stock
        )
        return self.products, stats

    def build_stats(self, fetched: int, filtered: int, final: int,
                    in_stock: int, out_of_stock: int) -> dict:
        """Build statistics dictionary for this store."""
        return {
            "name": self.store_name,
            "url": self.base_url,
            "platform": self.platform_name,
            "fetched": fetched,
            "filtered": filtered,
            "final": final,
            "inStock": in_stock,
            "outOfStock": out_of_stock,
            "error": self.error,
            "duration": round(self.duration, 2)
        }

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name (shopify, woocommerce, squarespace)."""
        pass
