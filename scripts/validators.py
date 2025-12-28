"""
Product validators for different e-commerce platforms.
Consolidates validation logic that was duplicated across platforms.
"""

from abc import ABC, abstractmethod
from config import MIN_PRICE
from filters import (
    is_excluded_by_title,
    is_excluded_by_tags,
    is_excluded_by_category,
    get_title_exclusion_match,
    get_tag_exclusion_match,
    get_category_exclusion_match,
)


class ProductValidator(ABC):
    """Base class for product validation across platforms."""

    @abstractmethod
    def get_price(self, product: dict) -> float:
        """Extract price from platform-specific product structure."""
        pass

    @abstractmethod
    def get_title(self, product: dict) -> str:
        """Extract title from platform-specific product structure."""
        pass

    @abstractmethod
    def get_categories(self, product: dict) -> list[str]:
        """Extract categories from platform-specific product structure."""
        pass

    @abstractmethod
    def get_tags(self, product: dict) -> list[str]:
        """Extract tags from platform-specific product structure."""
        pass

    def is_valid(self, product: dict) -> bool:
        """Check if product passes all validation rules."""
        # Check price
        try:
            price = self.get_price(product)
            if price < MIN_PRICE:
                return False
        except (ValueError, TypeError):
            return False

        # Check title
        title = self.get_title(product)
        if is_excluded_by_title(title):
            return False

        # Check categories
        for category in self.get_categories(product):
            if is_excluded_by_category(category):
                return False

        # Check tags (convert to tuple for cache hashability in filter)
        tags = tuple(self.get_tags(product))
        if is_excluded_by_tags(tags):
            return False

        return True

    def get_exclusion_reason(self, product: dict) -> dict | None:
        """Get the reason why a product was excluded.

        Returns dict with keys: type, keyword, category, title
        Or None if the product is not excluded.
        """
        title = self.get_title(product)

        # Check title exclusion
        match = get_title_exclusion_match(title)
        if match:
            keyword, category = match
            return {
                "type": "title",
                "keyword": keyword,
                "category": category,
                "title": title,
            }

        # Check category exclusion
        for cat in self.get_categories(product):
            match = get_category_exclusion_match(cat)
            if match:
                keyword, filter_category = match
                return {
                    "type": "category",
                    "keyword": keyword,
                    "category": filter_category,
                    "title": title,
                }

        # Check tag exclusion
        tags = tuple(self.get_tags(product))
        match = get_tag_exclusion_match(tags)
        if match:
            keyword, category = match
            return {
                "type": "tag",
                "keyword": keyword,
                "category": category,
                "title": title,
            }

        return None


class ShopifyValidator(ProductValidator):
    """Validator for Shopify products."""

    def get_price(self, product: dict) -> float:
        variants = product.get("variants", [])
        if not variants:
            raise ValueError("No variants found")
        price = variants[0].get("price")
        if price is None:
            raise ValueError("No price in variant")
        return float(price)

    def get_title(self, product: dict) -> str:
        return product.get("title", "")

    def get_categories(self, product: dict) -> list[str]:
        product_type = product.get("product_type", "")
        return [product_type] if product_type else []

    def get_tags(self, product: dict) -> list[str]:
        tags = product.get("tags", [])
        if isinstance(tags, str):
            return [t.strip() for t in tags.split(",")]
        return tags


class WooCommerceValidator(ProductValidator):
    """Validator for WooCommerce products."""

    def get_price(self, product: dict) -> float:
        # WooCommerce prices are in cents
        prices = product.get("prices", {})
        price = prices.get("price")
        if price is None:
            raise ValueError("No price found")
        return int(price) / 100

    def get_title(self, product: dict) -> str:
        return product.get("name", "")

    def get_categories(self, product: dict) -> list[str]:
        return [cat.get("name", "") for cat in product.get("categories", [])]

    def get_tags(self, product: dict) -> list[str]:
        return [tag.get("name", "") for tag in product.get("tags", [])]


class SquarespaceValidator(ProductValidator):
    """Validator for Squarespace products."""

    def get_price(self, product: dict) -> float:
        variants = product.get("structuredContent", {}).get("variants", [])
        if not variants:
            raise ValueError("No variants found")
        price = variants[0].get("priceMoney", {}).get("value")
        if price is None:
            raise ValueError("No price in variant")
        return float(price)

    def get_title(self, product: dict) -> str:
        return product.get("title", "")

    def get_categories(self, product: dict) -> list[str]:
        return product.get("categories", [])

    def get_tags(self, product: dict) -> list[str]:
        # Squarespace doesn't have separate tags, uses categories
        return []


# Factory function for getting validators
_validators = {
    "shopify": ShopifyValidator(),
    "woocommerce": WooCommerceValidator(),
    "squarespace": SquarespaceValidator(),
}


def get_validator(platform: str) -> ProductValidator:
    """Get the appropriate validator for a platform."""
    return _validators.get(platform, _validators["shopify"])
