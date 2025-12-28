"""
Shared utility functions for the Gel Blaster scraper.
"""

from typing import Any


def count_in_stock(products: list[dict]) -> int:
    """Count products that are in stock."""
    return sum(1 for p in products if p.get("inStock", False))


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default if conversion fails."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_first_variant(product: dict, variant_key: str = "variants") -> dict | None:
    """
    Safely get the first variant from a product.

    Args:
        product: Product dict
        variant_key: Key to access variants (e.g., "variants" or nested path)

    Returns:
        First variant dict or None if no variants
    """
    variants = product.get(variant_key, [])
    return variants[0] if variants else None


def get_nested_first_variant(product: dict, *keys: str) -> dict | None:
    """
    Get first variant from a nested structure.

    Args:
        product: Product dict
        *keys: Keys to traverse (e.g., "structuredContent", "variants")

    Returns:
        First variant dict or None if not found
    """
    current = product
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key, {})
    if isinstance(current, list) and current:
        return current[0]
    return None


def safe_get_image(product: dict, image_key: str = "images") -> str | None:
    """
    Safely extract the first image URL from a product.

    Args:
        product: Product dict
        image_key: Key to access images list

    Returns:
        Image URL string or None
    """
    images = product.get(image_key, [])
    if images and isinstance(images, list):
        first = images[0]
        if isinstance(first, dict):
            return first.get("src") or first.get("url")
        elif isinstance(first, str):
            return first
    return None


def normalize_store_url(url: str) -> str:
    """Normalize store URL by removing trailing slashes."""
    return url.rstrip("/") if url else ""


def build_error_stats(
    store_name: str,
    store_url: str,
    platform: str,
    error: str,
    duration: float = 0
) -> dict:
    """
    Build a stats dict for a store that failed to fetch.

    Args:
        store_name: Name of the store
        store_url: URL of the store
        platform: Platform type (shopify, woocommerce, squarespace)
        error: Error message
        duration: Time spent before failure

    Returns:
        Stats dict with error information
    """
    return {
        "name": store_name,
        "url": store_url,
        "platform": platform,
        "fetched": 0,
        "filtered": 0,
        "final": 0,
        "inStock": 0,
        "outOfStock": 0,
        "error": error,
        "duration": round(duration, 2),
        "logs": [{"time": "error", "level": "ERROR", "message": error}]
    }
