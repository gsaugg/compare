"""
Base fetcher class for e-commerce platforms.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import requests

from config import REQUEST_DELAY, REQUEST_TIMEOUT, USER_AGENT, MAX_PAGES
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
        - _handle_rate_limit(response): Handle rate limiting (optional)
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

            try:
                response = self._make_request(url)

                # Let subclass handle rate limiting
                response = self._handle_rate_limit(response, url)
                if response is None:
                    break  # Subclass decided to stop

                response.raise_for_status()
                data = self._parse_response(response)

            except requests.RequestException as e:
                self.log.error(f"Page {page} failed: {e}")
                self.error = str(e)
                break
            except json.JSONDecodeError as e:
                self.log.error(f"JSON parse error: {e}")
                self.error = str(e)
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

    def _handle_rate_limit(self, response: requests.Response, url: str) -> requests.Response | None:
        """Handle rate limiting. Override for platform-specific handling."""
        return response  # Default: no rate limit handling

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
