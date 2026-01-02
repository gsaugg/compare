import Fuse, { type IFuseOptions } from 'fuse.js';
import type { Product } from '$lib/data/types';

// Search configuration
const FUSE_THRESHOLD = 0.3; // 0 = exact, 1 = match anything
const MIN_MATCH_LENGTH = 2;

// Extended product with normalized search field
interface SearchableProduct extends Product {
	_searchText: string;
}

// Cache for search results
const searchCache = new Map<string, Product[]>();
const MAX_CACHE_SIZE = 50;

/**
 * Normalize text for search matching.
 * Converts hyphens/dashes to spaces so "KS-1", "KS 1", and "KS1" all match.
 * Returns both spaced and compact versions for comprehensive matching.
 */
function normalizeForSearch(text: string): string {
	if (!text) return '';

	const withSpaces = text
		.replace(/[-–—]/g, ' ') // Replace hyphens/dashes with spaces
		.replace(/\s+/g, ' ') // Collapse multiple spaces
		.toLowerCase()
		.trim();

	// Include compact version (no spaces) to match "KS1" against "KS-1"
	const compact = withSpaces.replace(/\s+/g, '');

	return `${withSpaces} ${compact}`;
}

/**
 * Normalize search query
 */
function normalizeQuery(query: string): string {
	return query.replace(/[-–—]/g, ' ').replace(/\s+/g, ' ').toLowerCase().trim();
}

// Fuse instance (lazily initialized)
let fuseInstance: Fuse<SearchableProduct> | null = null;
let indexedProducts: Product[] | null = null;

// Pre-computed search text cache for word-based search
let searchTextCache: Map<string, string> | null = null;

/**
 * Build or rebuild the Fuse.js index and search text cache
 */
function buildIndex(products: Product[]): Fuse<SearchableProduct> {
	// Build search text cache for word-based search
	searchTextCache = new Map();

	// Add normalized search text to each product (include tags and SKUs)
	const searchableProducts: SearchableProduct[] = products.map((product) => {
		const searchText = buildSearchText(product);
		searchTextCache!.set(product.id, searchText);
		return {
			...product,
			_searchText: searchText
		};
	});

	const options: IFuseOptions<SearchableProduct> = {
		keys: [
			{ name: '_searchText', weight: 1.0 }, // Normalized field for hyphen/space matching
			{ name: 'title', weight: 0.7 }, // Original title for exact matches
			{ name: 'category', weight: 0.3 },
			{ name: 'tags', weight: 0.2 } // Tags with low weight to avoid noise
		],
		threshold: FUSE_THRESHOLD,
		ignoreLocation: true, // Critical: match anywhere in string, not just first 60 chars
		includeScore: true,
		minMatchCharLength: MIN_MATCH_LENGTH,
		useExtendedSearch: true // Enable operators: 'exact, ^prefix, !exclude, |or
	};

	return new Fuse(searchableProducts, options);
}

/**
 * Get or create Fuse instance
 */
function getFuse(products: Product[]): Fuse<SearchableProduct> {
	// Rebuild index if products changed
	if (fuseInstance === null || indexedProducts !== products) {
		fuseInstance = buildIndex(products);
		indexedProducts = products;
		searchCache.clear(); // Clear cache when index changes
	}
	return fuseInstance;
}

/**
 * Build searchable text for a product (title + category + SKUs + tags)
 */
function buildSearchText(product: Product): string {
	const skus = product.vendors
		.map((v) => v.sku)
		.filter(Boolean)
		.join(' ');
	return normalizeForSearch(
		`${product.title} ${product.category || ''} ${skus} ${(product.tags || []).join(' ')}`
	);
}

/**
 * Ensure search text cache is built
 */
function ensureSearchTextCache(products: Product[]): void {
	if (searchTextCache === null || indexedProducts !== products) {
		// Build cache if not exists or products changed
		searchTextCache = new Map();
		for (const product of products) {
			searchTextCache.set(product.id, buildSearchText(product));
		}
		indexedProducts = products;
	}
}

/**
 * Word-based matching (all words must appear in searchable text)
 * This is faster and more predictable for simple searches
 */
function wordBasedSearch(products: Product[], query: string): Product[] {
	const normalizedQuery = normalizeQuery(query);
	const searchWords = normalizedQuery.split(/\s+/).filter((w) => w.length >= MIN_MATCH_LENGTH);

	if (searchWords.length === 0) return products;

	// Ensure cache is built
	ensureSearchTextCache(products);

	return products.filter((product) => {
		const searchText = searchTextCache!.get(product.id) || '';
		return searchWords.every((word) => searchText.includes(word));
	});
}

/**
 * Search products using hybrid approach:
 * 1. First try word-based matching (fast, predictable)
 * 2. Fall back to Fuse.js fuzzy search if no results
 */
export function searchProducts(products: Product[], query: string): Product[] {
	const trimmedQuery = query.trim();

	// Empty query returns all products
	if (!trimmedQuery) return products;

	// Check cache
	const cacheKey = `${products.length}:${trimmedQuery}`;
	if (searchCache.has(cacheKey)) {
		return searchCache.get(cacheKey)!;
	}

	let results: Product[];

	// Check if query uses extended search operators
	const hasExtendedOperators = /^['=^!]|[|]/.test(trimmedQuery);

	if (hasExtendedOperators) {
		// Use Fuse.js directly for extended search
		const fuse = getFuse(products);
		const fuseResults = fuse.search(trimmedQuery);
		results = fuseResults.map((r) => {
			// Remove the _searchText field from results
			const { _searchText, ...product } = r.item;
			return product as Product;
		});
	} else {
		// Try word-based search first (faster, more predictable)
		const wordResults = wordBasedSearch(products, trimmedQuery);

		if (wordResults.length > 0) {
			results = wordResults;
		} else {
			// Fall back to fuzzy search
			const fuse = getFuse(products);
			const fuseResults = fuse.search(normalizeQuery(trimmedQuery));
			results = fuseResults.map((r) => {
				const { _searchText, ...product } = r.item;
				return product as Product;
			});
		}
	}

	// Cache results (with size limit)
	if (searchCache.size >= MAX_CACHE_SIZE) {
		// Remove oldest entry
		const firstKey = searchCache.keys().next().value;
		if (firstKey) searchCache.delete(firstKey);
	}
	searchCache.set(cacheKey, results);

	return results;
}

/**
 * Clear the search cache and index
 */
export function clearSearchCache(): void {
	searchCache.clear();
	fuseInstance = null;
	indexedProducts = null;
	searchTextCache = null;
}
