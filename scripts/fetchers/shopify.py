"""
Shopify store fetcher.
"""

import time
from typing import Any

import requests

from config import SHOPIFY_REQUEST_DELAY
from fetchers.base import BaseFetcher


class ShopifyFetcher(BaseFetcher):
    """Fetcher for Shopify stores using the /products.json endpoint."""

    @property
    def platform_name(self) -> str:
        return "shopify"

    def _build_page_url(self, page: int) -> str:
        return f"{self.base_url}/products.json?limit=250&page={page}"

    def _extract_products(self, data: Any) -> list:
        return data.get("products", [])

    def _delay(self) -> None:
        """Use longer delay for Shopify to avoid rate limits."""
        time.sleep(SHOPIFY_REQUEST_DELAY)

    def _handle_rate_limit(self, response: requests.Response, url: str) -> requests.Response | None:
        """Handle Shopify 429 rate limiting with Retry-After header."""
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 30))
            self.log.warning(f"Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after)
            # Retry once
            return self._make_request(url)
        return response
