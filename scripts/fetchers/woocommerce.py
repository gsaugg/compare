"""
WooCommerce store fetcher.

Handles both simple products and variable products with variations.
"""

import time
from typing import Any

import requests

from fetchers.base import BaseFetcher
from config import REQUEST_DELAY


class WooCommerceFetcher(BaseFetcher):
    """Fetcher for WooCommerce stores using the Store API.

    Fetches both simple products and variations:
    1. Fetch products (type=simple,variable)
    2. Build parent lookup for categories
    3. Fetch variations (?type=variation)
    4. Enrich variations with parent data
    5. Return simple products + enriched variations
    """

    def __init__(self, store_name: str, base_url: str):
        super().__init__(store_name, base_url)
        self.api_path = None  # Detected in _setup()
        self.per_page = 100
        self.fetch_variations = True  # Can be disabled for testing

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

    def fetch(self) -> tuple[list, dict]:
        """Fetch all products including variations.

        Overrides base fetch to add variation fetching.
        """
        # First, fetch products using the standard method
        products, stats = super().fetch()

        if not self.fetch_variations:
            return products, stats

        # Build parent lookup for variable products
        parent_lookup = {}
        simple_products = []
        variable_count = 0

        for p in products:
            product_type = p.get("type", "simple")
            if product_type == "variable":
                # Save for category lookup
                parent_lookup[p["id"]] = {
                    "name": p.get("name", ""),
                    "categories": p.get("categories", []),
                    "images": p.get("images", []),
                    "tags": p.get("tags", []),
                }
                variable_count += 1
            else:
                # Keep simple products
                simple_products.append(p)

        # Fetch variations if there are variable products
        variations = []
        if variable_count > 0:
            self.log.info(f"Found {variable_count} variable products, fetching variations...")
            variations = self._fetch_variations()

            # Enrich variations with parent data
            enriched = 0
            for v in variations:
                parent_id = v.get("parent")
                parent = parent_lookup.get(parent_id)
                if parent:
                    # Inherit categories from parent
                    if not v.get("categories"):
                        v["categories"] = parent["categories"]
                    # Inherit tags from parent
                    if not v.get("tags"):
                        v["tags"] = parent["tags"]
                    enriched += 1

            self.log.info(f"Fetched {len(variations)} variations, enriched {enriched}")

        # Combine simple products + variations
        all_products = simple_products + variations

        # Update stats
        stats["simple"] = len(simple_products)
        stats["variable"] = variable_count
        stats["variations"] = len(variations)
        stats["final"] = len(all_products)

        self.log.info(
            f"Total: {len(simple_products)} simple + {len(variations)} variations = {len(all_products)}"
        )

        return all_products, stats

    def _fetch_variations(self) -> list:
        """Fetch all variations using ?type=variation query."""
        variations = []
        page = 1

        while True:
            url = f"{self.base_url}{self.api_path}?type=variation&per_page={self.per_page}&page={page}"

            try:
                response = self._make_request(url)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                self.log.error(f"Failed to fetch variations page {page}: {e}")
                break
            except ValueError as e:
                self.log.error(f"JSON parse error on variations page {page}: {e}")
                break

            if not data:
                break

            variations.extend(data)
            self.log.info(f"Variations page {page}: {len(data)} items")

            if len(data) < self.per_page:
                break

            page += 1
            time.sleep(REQUEST_DELAY)

        return variations
