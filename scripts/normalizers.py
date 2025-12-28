"""
Product normalizers for different e-commerce platforms.
Consolidates normalization logic that was duplicated across platforms.
"""

import html
from abc import ABC, abstractmethod
from categories import get_best_category


def safe_print(*args, **kwargs):
    """Thread-safe print - imported from scrape.py at runtime to avoid circular import."""
    print(*args, **kwargs)


class ProductNormalizer(ABC):
    """Base class for normalizing products to a common schema."""

    def __init__(self, store_name: str, store_url: str):
        self.store_name = store_name
        self.store_url = store_url
        self.store_id_prefix = store_name.lower().replace(" ", "-")

    @abstractmethod
    def get_id(self, product: dict) -> str:
        """Extract product ID from platform-specific structure."""
        pass

    @abstractmethod
    def get_title(self, product: dict) -> str:
        """Extract and clean title from platform-specific structure."""
        pass

    @abstractmethod
    def get_price(self, product: dict) -> float:
        """Extract current price from platform-specific structure."""
        pass

    @abstractmethod
    def get_compare_price(self, product: dict) -> float | None:
        """Extract compare/original price if on sale."""
        pass

    @abstractmethod
    def get_image(self, product: dict) -> str | None:
        """Extract image URL from platform-specific structure."""
        pass

    @abstractmethod
    def get_url(self, product: dict) -> str:
        """Build product URL from platform-specific structure."""
        pass

    @abstractmethod
    def get_tags(self, product: dict) -> list[str]:
        """Extract tags from platform-specific structure."""
        pass

    @abstractmethod
    def get_raw_category(self, product: dict) -> str:
        """Extract raw category from platform-specific structure."""
        pass

    @abstractmethod
    def get_in_stock(self, product: dict) -> bool:
        """Check if product is in stock."""
        pass

    def normalize(self, product: dict) -> dict | None:
        """Normalize a product to the common schema."""
        try:
            title = self.get_title(product)
            tags = self.get_tags(product)
            raw_category = self.get_raw_category(product)
            category = get_best_category(raw_category, title, tags)

            return {
                "id": f"{self.store_id_prefix}-{self.get_id(product)}",
                "title": title,
                "price": self.get_price(product),
                "comparePrice": self.get_compare_price(product),
                "image": self.get_image(product),
                "url": self.get_url(product),
                "vendor": self.store_name,
                "category": category,
                "tags": tags[:10],  # Limit tags
                "inStock": self.get_in_stock(product),
            }
        except (KeyError, ValueError, TypeError) as e:
            safe_print(f"  Warning: Could not normalize product: {e}")
            return None


class ShopifyNormalizer(ProductNormalizer):
    """Normalizer for Shopify products."""

    def get_id(self, product: dict) -> str:
        return str(product["id"])

    def get_title(self, product: dict) -> str:
        return product.get("title", "Unknown")

    def get_price(self, product: dict) -> float:
        variants = product.get("variants", [])
        if not variants:
            return 0
        return float(variants[0].get("price", 0))

    def get_compare_price(self, product: dict) -> float | None:
        variants = product.get("variants", [])
        if not variants:
            return None
        compare_price = variants[0].get("compare_at_price")
        return float(compare_price) if compare_price else None

    def get_image(self, product: dict) -> str | None:
        images = product.get("images", [])
        return images[0]["src"] if images else None

    def get_url(self, product: dict) -> str:
        handle = product.get("handle", "")
        return f"{self.store_url}/products/{handle}"

    def get_tags(self, product: dict) -> list[str]:
        tags = product.get("tags", [])
        if isinstance(tags, str):
            return [t.strip() for t in tags.split(",") if t.strip()]
        return tags

    def get_raw_category(self, product: dict) -> str:
        return product.get("product_type", "").strip()

    def get_in_stock(self, product: dict) -> bool:
        variants = product.get("variants", [])
        return any(v.get("available", False) for v in variants)


class WooCommerceNormalizer(ProductNormalizer):
    """Normalizer for WooCommerce products."""

    def get_id(self, product: dict) -> str:
        return str(product["id"])

    def get_title(self, product: dict) -> str:
        # Decode HTML entities (e.g., &#8211; -> –)
        return html.unescape(product.get("name", "Unknown"))

    def get_price(self, product: dict) -> float:
        # WooCommerce prices are in cents
        return int(product.get("prices", {}).get("price", 0)) / 100

    def get_compare_price(self, product: dict) -> float | None:
        prices = product.get("prices", {})
        price = int(prices.get("price", 0)) / 100
        regular_price = int(prices.get("regular_price", 0)) / 100
        # Compare price only if there's a discount
        return regular_price if regular_price > price else None

    def get_image(self, product: dict) -> str | None:
        images = product.get("images", [])
        return images[0]["src"] if images else None

    def get_url(self, product: dict) -> str:
        return product.get("permalink", "")

    def get_tags(self, product: dict) -> list[str]:
        return [t.get("name", "") for t in product.get("tags", [])]

    def get_raw_category(self, product: dict) -> str:
        categories = product.get("categories", [])
        return categories[0]["name"] if categories else ""

    def get_in_stock(self, product: dict) -> bool:
        return product.get("is_in_stock", False)


class SquarespaceNormalizer(ProductNormalizer):
    """Normalizer for Squarespace products."""

    def get_id(self, product: dict) -> str:
        return str(product.get("id", ""))

    def get_title(self, product: dict) -> str:
        return product.get("title", "Unknown")

    def _get_variant(self, product: dict) -> dict:
        """Get the first variant for price/stock info."""
        return product.get("structuredContent", {}).get("variants", [{}])[0]

    def get_price(self, product: dict) -> float:
        variant = self._get_variant(product)
        price = float(variant.get("priceMoney", {}).get("value", 0))
        sale_price_str = variant.get("salePriceMoney", {}).get("value", "0")
        sale_price = float(sale_price_str) if sale_price_str else 0

        # If sale price exists and is less than regular, use sale price
        if sale_price > 0 and sale_price < price:
            return sale_price
        return price

    def get_compare_price(self, product: dict) -> float | None:
        variant = self._get_variant(product)
        price = float(variant.get("priceMoney", {}).get("value", 0))
        sale_price_str = variant.get("salePriceMoney", {}).get("value", "0")
        sale_price = float(sale_price_str) if sale_price_str else 0

        # Compare price is the original if on sale
        if sale_price > 0 and sale_price < price:
            return price
        return None

    def get_image(self, product: dict) -> str | None:
        return product.get("assetUrl")

    def get_url(self, product: dict) -> str:
        url_id = product.get("urlId", "")
        return f"{self.store_url}/store/{url_id}" if url_id else ""

    def get_tags(self, product: dict) -> list[str]:
        # Squarespace uses categories as tags
        return product.get("categories", [])[:10]

    def get_raw_category(self, product: dict) -> str:
        categories = product.get("categories", [])
        return categories[0] if categories else ""

    def get_in_stock(self, product: dict) -> bool:
        variant = self._get_variant(product)
        stock = variant.get("qtyInStock", 0)
        unlimited = variant.get("unlimited", False)
        return unlimited or stock > 0


def get_normalizer(platform: str, store_name: str, store_url: str) -> ProductNormalizer:
    """Get the appropriate normalizer for a platform."""
    normalizers = {
        "shopify": ShopifyNormalizer,
        "woocommerce": WooCommerceNormalizer,
        "squarespace": SquarespaceNormalizer,
    }
    normalizer_class = normalizers.get(platform, ShopifyNormalizer)
    return normalizer_class(store_name, store_url)
