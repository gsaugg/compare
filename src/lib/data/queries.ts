// TanStack Query wrappers for data fetching
// Note: Svelte 5 + TanStack Query v6 requires options wrapped in a function
import { createQuery } from '@tanstack/svelte-query';
import { dataProvider } from './static';
import type { ProductsData, TrackerDataResponse, Stats } from './types';

// Products query - main data for the product grid
export function productsQuery() {
	return createQuery(() => ({
		queryKey: ['products'] as const,
		queryFn: () => dataProvider.getProducts(),
		staleTime: 1000 * 60 * 60, // Fresh for 1 hour
		refetchOnWindowFocus: true // Refresh when user returns to tab
	}));
}

// Tracker data query - price history for charts
export function trackerDataQuery() {
	return createQuery(() => ({
		queryKey: ['tracker-data'] as const,
		queryFn: () => dataProvider.getTrackerData(),
		staleTime: 1000 * 60 * 60,
		refetchOnWindowFocus: true
	}));
}

// Stats query - scraper status dashboard
export function statsQuery() {
	return createQuery(() => ({
		queryKey: ['stats'] as const,
		queryFn: () => dataProvider.getStats(),
		staleTime: 1000 * 60 * 60,
		refetchOnWindowFocus: true
	}));
}
