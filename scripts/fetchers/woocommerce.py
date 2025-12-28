"""
WooCommerce store fetcher.
"""

from typing import Any

import requests

from fetchers.base import BaseFetcher


class WooCommerceFetcher(BaseFetcher):
    """Fetcher for WooCommerce stores using the Store API."""

    def __init__(self, store_name: str, base_url: str):
        super().__init__(store_name, base_url)
        self.api_path = None  # Detected in _setup()
        self.per_page = 100

    @property
    def platform_name(self) -> str:
        return "woocommerce"

    def _setup(self) -> None:
        """Detect the correct WooCommerce API path before fetching."""
        self.api_path = self._detect_api_path()

    def _detect_api_path(self) -> str:
        """Detect which WooCommerce API path is available."""
        api_paths = [
            "/wp-json/wc/store/v1/products",
            "/wp-json/wc/store/products"
        ]

        for path in api_paths:
            try:
                test_url = f"{self.base_url}{path}?per_page=1"
                response = self._make_request(test_url, timeout=10)
                if response.status_code == 200:
                    return path
            except requests.RequestException:
                continue

        # Default to v1 path
        return "/wp-json/wc/store/v1/products"

    def _build_page_url(self, page: int) -> str:
        return f"{self.base_url}{self.api_path}?per_page={self.per_page}&page={page}"

    def _extract_products(self, data: Any) -> list:
        # WooCommerce returns array directly
        return data if isinstance(data, list) else []

    def _is_last_page(self, data: Any, page: int, products: list) -> bool:
        """WooCommerce: last page when fewer products than per_page."""
        return len(products) < self.per_page
