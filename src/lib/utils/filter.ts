import type { Product } from '$lib/data/types';
import type { FilterState } from '$lib/stores/filters.svelte';
import { searchProducts } from '$lib/search/fuse';

export function filterProducts(products: Product[], filters: FilterState): Product[] {
	let result = products;

	// Search filter (Fuse.js with fuzzy matching and extended search)
	if (filters.search) {
		result = searchProducts(result, filters.search);
	}

	// Category filter
	if (filters.categories.length > 0) {
		result = result.filter(
			(product) => product.category && filters.categories.includes(product.category)
		);
	}

	// Store filter
	if (filters.stores.length > 0) {
		result = result.filter((product) =>
			product.vendors.some((v) => filters.stores.includes(v.name))
		);
	}

	// Price range filter
	if (filters.minPrice !== null) {
		result = result.filter((product) => product.lowestPrice >= filters.minPrice!);
	}
	if (filters.maxPrice !== null) {
		result = result.filter((product) => product.lowestPrice <= filters.maxPrice!);
	}

	// In stock filter
	if (filters.inStockOnly) {
		result = result.filter((product) => product.inStock);
	}

	// On sale filter
	if (filters.onSaleOnly) {
		result = result.filter((product) =>
			product.vendors.some((v) => v.regularPrice && v.price < v.regularPrice)
		);
	}

	// Sort
	result = sortProducts(result, filters.sortBy);

	return result;
}

function sortProducts(products: Product[], sortBy: FilterState['sortBy']): Product[] {
	const sorted = [...products];

	switch (sortBy) {
		case 'price-asc':
			sorted.sort((a, b) => a.lowestPrice - b.lowestPrice);
			break;
		case 'price-desc':
			sorted.sort((a, b) => b.lowestPrice - a.lowestPrice);
			break;
		case 'name-asc':
			sorted.sort((a, b) => a.title.localeCompare(b.title));
			break;
		case 'name-desc':
			sorted.sort((a, b) => b.title.localeCompare(a.title));
			break;
		case 'newest':
			// Products don't have a date field, so this is a no-op for now
			break;
	}

	return sorted;
}

export function extractCategories(products: Product[]): string[] {
	const categories = new Set<string>();
	for (const product of products) {
		if (product.category) {
			categories.add(product.category);
		}
	}
	return Array.from(categories).sort();
}

export function extractStores(products: Product[]): string[] {
	const stores = new Set<string>();
	for (const product of products) {
		for (const vendor of product.vendors) {
			stores.add(vendor.name);
		}
	}
	return Array.from(stores).sort();
}
