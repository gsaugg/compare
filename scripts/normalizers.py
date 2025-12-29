"""
Product normalizers for different e-commerce platforms.
Consolidates normalization logic that was duplicated across platforms.
"""

import html
import re
from abc import ABC, abstractmethod
from categories import get_best_category

# SEO spam patterns to strip from titles
TITLE_CLEANUP_PATTERNS = [
    r"\s*-\s*(Parts\s*&\s*Accessories\s*)?Gel Blaster[s]?\s*(Guns,?\s*)?(Pistols,?\s*)?(Handguns\s*)?(Rifles\s*)?(For Sale)?",
    r"\s*-\s*Gel Blaster\s*(Parts\s*&\s*Accessories\s*)?(For Sale)?",
    r"\s*-\s*For Sale\s*$",
    r"\s*\|\s*.*$",  # Strip anything after pipe
]


def clean_title(title: str) -> str:
    """Remove SEO spam from product titles."""
    for pattern in TITLE_CLEANUP_PATTERNS:
        title = re.sub(pattern, "", title, flags=re.IGNORECASE)
    return title.strip()


def safe_print(*args, **kwargs):
    """Thread-safe print - imported from scrape.py at runtime to avoid circular import."""
    print(*args, **kwargs)


class ProductNormalizer(ABC):
    """Base class for normalizing products to a common schema."""

    def __init__(self, store_name: str, store_url: str, store_id: str = None):
        self.store_name = store_name
        self.store_url = store_url
        self.store_id = store_id or store_name.lower().replace(" ", "-")
        # Keep for backwards compatibility
        self.store_id_prefix = store_name.lower().replace(" ", "-")

    @abstractmethod
    def get_id(self, product: dict) -> str:
        """Extract product ID from platform-specific structure."""
        pass

    @abstractmethod
    def get_sku(self, product: dict, variant: dict = None) -> str | None:
        """Extract SKU from platform-specific structure."""
        pass

    @abstractmethod
    def get_variant_id(self, product: dict, variant: dict = None) -> str:
        """Extract variant ID from platform-specific structure."""
        pass

    def get_item_id(self, product: dict, variant: dict = None) -> str:
        """Build the composite item ID: storeId|productId|variantId."""
        product_id = self.get_id(product)
        variant_id = self.get_variant_id(product, variant)
        return f"{self.store_id}|{product_id}|{variant_id}"

    @abstractmethod
    def get_variants(self, product: dict) -> list[dict]:
        """Get all variants for a product. Returns list with single empty dict if no variants."""
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

    @abstractmethod
    def get_variant_title(self, product: dict, variant: dict) -> str:
        """Get the variant-specific portion of the title (e.g., 'Red', 'Large')."""
        pass

    @abstractmethod
    def get_variant_price(self, product: dict, variant: dict) -> float:
        """Extract price for a specific variant."""
        pass

    @abstractmethod
    def get_variant_compare_price(self, product: dict, variant: dict) -> float | None:
        """Extract compare price for a specific variant."""
        pass

    @abstractmethod
    def get_variant_in_stock(self, product: dict, variant: dict) -> bool:
        """Check if a specific variant is in stock."""
        pass

    @abstractmethod
    def get_variant_image(self, product: dict, variant: dict) -> str | None:
        """Get variant-specific image or fall back to product image."""
        pass

    def normalize(self, product: dict) -> dict | None:
        """Normalize a product to the common schema (legacy single-product format)."""
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

    def normalize_all(self, product: dict) -> list[dict]:
        """Normalize a product to items (one per variant).

        Returns a list of normalized items, each with a unique item ID.
        """
        items = []
        base_title = self.get_title(product)
        tags = self.get_tags(product)
        raw_category = self.get_raw_category(product)
        category = get_best_category(raw_category, base_title, tags)

        for variant in self.get_variants(product):
            try:
                # Build full title with variant option
                variant_title = self.get_variant_title(product, variant)
                if variant_title and variant_title.lower() != "default title":
                    title = f"{base_title} - {variant_title}"
                else:
                    title = base_title

                item = {
                    "id": self.get_item_id(product, variant),
                    "storeId": self.store_id,
                    "productId": str(self.get_id(product)),
                    "variantId": str(self.get_variant_id(product, variant)),
                    "title": title,
                    "sku": self.get_sku(product, variant),
                    "price": self.get_variant_price(product, variant),
                    "comparePrice": self.get_variant_compare_price(product, variant),
                    "image": self.get_variant_image(product, variant),
                    "url": self.get_url(product),
                    "vendor": self.store_name,
                    "category": category,
                    "tags": tags[:10],
                    "inStock": self.get_variant_in_stock(product, variant),
                }
                items.append(item)
            except (KeyError, ValueError, TypeError) as e:
                safe_print(f"  Warning: Could not normalize variant: {e}")
                continue

        return items


class ShopifyNormalizer(ProductNormalizer):
    """Normalizer for Shopify products."""

    def get_id(self, product: dict) -> str:
        return str(product["id"])

    def get_sku(self, product: dict, variant: dict = None) -> str | None:
        if variant:
            return variant.get("sku") or None
        variants = product.get("variants", [])
        return variants[0].get("sku") if variants else None

    def get_variant_id(self, product: dict, variant: dict = None) -> str:
        if variant:
            return str(variant.get("id", self.get_id(product)))
        variants = product.get("variants", [])
        return str(variants[0]["id"]) if variants else self.get_id(product)

    def get_variants(self, product: dict) -> list[dict]:
        variants = product.get("variants", [])
        return variants if variants else [{}]

    def get_title(self, product: dict) -> str:
        title = product.get("title", "Unknown")
        return clean_title(title)

    def get_variant_title(self, product: dict, variant: dict) -> str:
        return variant.get("title", "")

    def get_price(self, product: dict) -> float:
        variants = product.get("variants", [])
        if not variants:
            return 0
        return float(variants[0].get("price", 0))

    def get_variant_price(self, product: dict, variant: dict) -> float:
        return float(variant.get("price", 0))

    def get_compare_price(self, product: dict) -> float | None:
        variants = product.get("variants", [])
        if not variants:
            return None
        compare_price = variants[0].get("compare_at_price")
        return float(compare_price) if compare_price else None

    def get_variant_compare_price(self, product: dict, variant: dict) -> float | None:
        compare_price = variant.get("compare_at_price")
        return float(compare_price) if compare_price else None

    def get_image(self, product: dict) -> str | None:
        images = product.get("images", [])
        return images[0]["src"] if images else None

    def get_variant_image(self, product: dict, variant: dict) -> str | None:
        # Variant may have featured_image
        featured = variant.get("featured_image")
        if featured and featured.get("src"):
            return featured["src"]
        # Fall back to product image
        return self.get_image(product)

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

    def get_variant_in_stock(self, product: dict, variant: dict) -> bool:
        return variant.get("available", False)


class WooCommerceNormalizer(ProductNormalizer):
    """Normalizer for WooCommerce products.

    Handles both simple products and variations (fetched separately).
    For variations, the product has: type='variation', parent=<product_id>, variation='Colour: Black'
    For simple products, we use productId as variantId.
    """

    def get_id(self, product: dict) -> str:
        # For variations, this returns the variation ID
        # For simple/variable products, this returns the product ID
        return str(product["id"])

    def get_sku(self, product: dict, variant: dict = None) -> str | None:
        # WooCommerce has SKU directly on product (or variation)
        sku = product.get("sku")
        if not sku:
            return None
        # Decode HTML entities (e.g., &#8243; -> ″)
        return html.unescape(sku)

    def get_variant_id(self, product: dict, variant: dict = None) -> str:
        # For variations, use the product's own ID (which is the variation ID)
        # For simple products, use productId as variantId
        product_id = str(product["id"])
        if product.get("type") == "variation":
            # This IS a variation, its ID is the variant ID
            return product_id
        # Simple product - use product ID as variant ID
        return product_id

    def get_variants(self, product: dict) -> list[dict]:
        # WooCommerce variations are fetched separately, so each product is its own "variant"
        return [product]

    def get_title(self, product: dict) -> str:
        # Decode HTML entities (e.g., &#8211; -> –)
        return html.unescape(product.get("name", "Unknown"))

    def get_variant_title(self, product: dict, variant: dict) -> str:
        # For variations, extract value from "Colour: Black" format
        variation_str = product.get("variation", "")
        if variation_str and ":" in variation_str:
            # Extract just the value part
            return variation_str.split(":", 1)[1].strip()
        return variation_str

    def get_price(self, product: dict) -> float:
        # WooCommerce prices are in cents
        return int(product.get("prices", {}).get("price", 0)) / 100

    def get_variant_price(self, product: dict, variant: dict) -> float:
        return self.get_price(product)

    def get_compare_price(self, product: dict) -> float | None:
        prices = product.get("prices", {})
        price = int(prices.get("price", 0)) / 100
        regular_price = int(prices.get("regular_price", 0)) / 100
        # Compare price only if there's a discount
        return regular_price if regular_price > price else None

    def get_variant_compare_price(self, product: dict, variant: dict) -> float | None:
        return self.get_compare_price(product)

    def get_image(self, product: dict) -> str | None:
        images = product.get("images", [])
        return images[0]["src"] if images else None

    def get_variant_image(self, product: dict, variant: dict) -> str | None:
        return self.get_image(product)

    def get_url(self, product: dict) -> str:
        return product.get("permalink", "")

    def get_tags(self, product: dict) -> list[str]:
        return [t.get("name", "") for t in product.get("tags", [])]

    def get_raw_category(self, product: dict) -> str:
        categories = product.get("categories", [])
        return categories[0]["name"] if categories else ""

    def get_in_stock(self, product: dict) -> bool:
        return product.get("is_in_stock", False)

    def get_variant_in_stock(self, product: dict, variant: dict) -> bool:
        return self.get_in_stock(product)


class SquarespaceNormalizer(ProductNormalizer):
    """Normalizer for Squarespace products."""

    def get_id(self, product: dict) -> str:
        return str(product.get("id", ""))

    def get_sku(self, product: dict, variant: dict = None) -> str | None:
        if variant:
            return variant.get("sku") or None
        v = self._get_variant(product)
        return v.get("sku") or None

    def get_variant_id(self, product: dict, variant: dict = None) -> str:
        if variant:
            return str(variant.get("id", self.get_id(product)))
        v = self._get_variant(product)
        return str(v.get("id", self.get_id(product)))

    def get_variants(self, product: dict) -> list[dict]:
        variants = product.get("structuredContent", {}).get("variants", [])
        return variants if variants else [{}]

    def get_title(self, product: dict) -> str:
        return product.get("title", "Unknown")

    def get_variant_title(self, product: dict, variant: dict) -> str:
        # Squarespace uses attributes dict like {'Pack Size': 'Single Shell'}
        attributes = variant.get("attributes", {})
        if attributes:
            # Join all attribute values
            return " / ".join(str(v) for v in attributes.values())
        return ""

    def _get_variant(self, product: dict) -> dict:
        """Get the first variant for price/stock info."""
        return product.get("structuredContent", {}).get("variants", [{}])[0]

    def _get_variant_price(self, variant: dict) -> float:
        """Get price from a variant, handling sale prices."""
        price = float(variant.get("priceMoney", {}).get("value", 0))
        sale_price_str = variant.get("salePriceMoney", {}).get("value", "0")
        sale_price = float(sale_price_str) if sale_price_str else 0

        # If sale price exists and is less than regular, use sale price
        if sale_price > 0 and sale_price < price:
            return sale_price
        return price

    def get_price(self, product: dict) -> float:
        variant = self._get_variant(product)
        return self._get_variant_price(variant)

    def get_variant_price(self, product: dict, variant: dict) -> float:
        return self._get_variant_price(variant)

    def _get_variant_compare_price(self, variant: dict) -> float | None:
        """Get compare price from a variant."""
        price = float(variant.get("priceMoney", {}).get("value", 0))
        sale_price_str = variant.get("salePriceMoney", {}).get("value", "0")
        sale_price = float(sale_price_str) if sale_price_str else 0

        # Compare price is the original if on sale
        if sale_price > 0 and sale_price < price:
            return price
        return None

    def get_compare_price(self, product: dict) -> float | None:
        variant = self._get_variant(product)
        return self._get_variant_compare_price(variant)

    def get_variant_compare_price(self, product: dict, variant: dict) -> float | None:
        return self._get_variant_compare_price(variant)

    def get_image(self, product: dict) -> str | None:
        return product.get("assetUrl")

    def get_variant_image(self, product: dict, variant: dict) -> str | None:
        # Squarespace variants may have their own image
        # For now, fall back to product image
        return self.get_image(product)

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

    def get_variant_in_stock(self, product: dict, variant: dict) -> bool:
        stock = variant.get("qtyInStock", 0)
        unlimited = variant.get("unlimited", False)
        return unlimited or stock > 0


def get_normalizer(
    platform: str, store_name: str, store_url: str, store_id: str = None
) -> ProductNormalizer:
    """Get the appropriate normalizer for a platform."""
    normalizers = {
        "shopify": ShopifyNormalizer,
        "woocommerce": WooCommerceNormalizer,
        "squarespace": SquarespaceNormalizer,
    }
    normalizer_class = normalizers.get(platform, ShopifyNormalizer)
    return normalizer_class(store_name, store_url, store_id)
