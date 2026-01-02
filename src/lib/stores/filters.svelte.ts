import { browser } from '$app/environment';
import { replaceState } from '$app/navigation';

// Filter state interface
export interface FilterState {
	search: string;
	categories: string[];
	stores: string[];
	minPrice: number | null;
	maxPrice: number | null;
	inStockOnly: boolean;
	onSaleOnly: boolean;
	sortBy:
		| 'discount-$'
		| 'discount-%'
		| 'price-asc'
		| 'price-desc'
		| 'name-asc'
		| 'name-desc'
		| 'newest';
}

// Default filter state
export const defaultFilters: FilterState = {
	search: '',
	categories: [],
	stores: [],
	minPrice: null,
	maxPrice: null,
	inStockOnly: true,
	onSaleOnly: false,
	sortBy: 'discount-$'
};

// Valid sort options for validation
const VALID_SORT_OPTIONS: FilterState['sortBy'][] = [
	'discount-$',
	'discount-%',
	'price-asc',
	'price-desc',
	'name-asc',
	'name-desc',
	'newest'
];

/**
 * Parse and validate a number from URL param
 * Returns null if invalid or NaN
 */
function parsePrice(value: string | null): number | null {
	if (!value) return null;
	const num = Number(value);
	return !isNaN(num) && isFinite(num) && num >= 0 ? num : null;
}

/**
 * Parse and validate sort option from URL param
 */
function parseSortBy(value: string | null): FilterState['sortBy'] {
	if (value && VALID_SORT_OPTIONS.includes(value as FilterState['sortBy'])) {
		return value as FilterState['sortBy'];
	}
	return 'discount-$';
}

/**
 * Parse filter state from URL parameters with validation
 */
function parseUrlParams(params: URLSearchParams): FilterState {
	return {
		search: params.get('q') || '',
		categories: params.get('cat')?.split(',').filter(Boolean) || [],
		stores: params.get('store')?.split(',').filter(Boolean) || [],
		minPrice: parsePrice(params.get('min')),
		maxPrice: parsePrice(params.get('max')),
		inStockOnly: params.get('instock') !== '0',
		onSaleOnly: params.get('sale') === '1',
		sortBy: parseSortBy(params.get('sort'))
	};
}

// Create reactive filter state with URL sync
function createFilterStore() {
	let state = $state<FilterState>({ ...defaultFilters });

	// Initialize from URL on browser
	if (browser) {
		const params = new URLSearchParams(window.location.search);
		state = parseUrlParams(params);
	}

	return {
		get value() {
			return state;
		},
		set value(newState: FilterState) {
			state = newState;
			if (browser) {
				syncToUrl(state);
			}
		},
		update(fn: (current: FilterState) => FilterState) {
			state = fn(state);
			if (browser) {
				syncToUrl(state);
			}
		},
		reset() {
			state = { ...defaultFilters };
			if (browser) {
				syncToUrl(state);
			}
		},
		syncFromUrl() {
			if (browser) {
				const params = new URLSearchParams(window.location.search);
				state = parseUrlParams(params);
			}
		},
		setSearch(search: string) {
			state = { ...state, search };
			if (browser) {
				syncToUrl(state);
			}
		},
		toggleCategory(category: string) {
			const categories = state.categories.includes(category)
				? state.categories.filter((c) => c !== category)
				: [...state.categories, category];
			state = { ...state, categories };
			if (browser) {
				syncToUrl(state);
			}
		},
		toggleStore(store: string) {
			const stores = state.stores.includes(store)
				? state.stores.filter((s) => s !== store)
				: [...state.stores, store];
			state = { ...state, stores };
			if (browser) {
				syncToUrl(state);
			}
		},
		setPriceRange(min: number | null, max: number | null) {
			state = { ...state, minPrice: min, maxPrice: max };
			if (browser) {
				syncToUrl(state);
			}
		},
		setInStockOnly(inStockOnly: boolean) {
			state = { ...state, inStockOnly };
			if (browser) {
				syncToUrl(state);
			}
		},
		setOnSaleOnly(onSaleOnly: boolean) {
			state = { ...state, onSaleOnly };
			if (browser) {
				syncToUrl(state);
			}
		},
		setSortBy(sortBy: FilterState['sortBy']) {
			state = { ...state, sortBy };
			if (browser) {
				syncToUrl(state);
			}
		}
	};
}

// Sync filter state to URL
function syncToUrl(state: FilterState) {
	const params = new URLSearchParams();

	if (state.search) params.set('q', state.search);
	if (state.categories.length) params.set('cat', state.categories.join(','));
	if (state.stores.length) params.set('store', state.stores.join(','));
	if (state.minPrice !== null) params.set('min', String(state.minPrice));
	if (state.maxPrice !== null) params.set('max', String(state.maxPrice));
	if (!state.inStockOnly) params.set('instock', '0');
	if (state.onSaleOnly) params.set('sale', '1');
	if (state.sortBy !== 'discount-$') params.set('sort', state.sortBy);

	const url = params.toString() ? `?${params.toString()}` : window.location.pathname;
	replaceState(url, {});
}

// Export singleton instance
export const filters = createFilterStore();
