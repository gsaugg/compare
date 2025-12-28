"""
Store fetchers for different e-commerce platforms.
"""

from fetchers.base import BaseFetcher
from fetchers.shopify import ShopifyFetcher
from fetchers.woocommerce import WooCommerceFetcher
from fetchers.squarespace import SquarespaceFetcher

__all__ = ['BaseFetcher', 'ShopifyFetcher', 'WooCommerceFetcher', 'SquarespaceFetcher']


def get_fetcher(platform: str, store_name: str, base_url: str) -> BaseFetcher:
    """Factory function to get the appropriate fetcher for a platform."""
    fetchers = {
        'shopify': ShopifyFetcher,
        'woocommerce': WooCommerceFetcher,
        'squarespace': SquarespaceFetcher,
    }

    fetcher_class = fetchers.get(platform.lower(), ShopifyFetcher)
    return fetcher_class(store_name, base_url)
