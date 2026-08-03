"""
Shopify store fetcher.
"""

import time
from typing import Any

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
