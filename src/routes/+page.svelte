<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import { dataProvider } from '$lib/data/static';
	import type { PricePoint, ProductPriceHistory } from '$lib/data/types';
	import VirtualProductGrid from '$lib/components/product/VirtualProductGrid.svelte';
	import FilterPanel from '$lib/components/filter/FilterPanel.svelte';
	import FilterSheet from '$lib/components/filter/FilterSheet.svelte';
	import { filters } from '$lib/stores/filters.svelte';
	import { viewMode } from '$lib/stores/viewMode.svelte';
	import { filterProducts, extractCategories, extractStores } from '$lib/utils/filter';
	import { page } from '$app/stores';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import * as Alert from '$lib/components/ui/alert';
	import { Progress } from '$lib/components/ui/progress';

	// Sync filters from URL when navigating to this page
	$effect(() => {
		// Subscribe to URL changes
		const url = $page.url;
		filters.syncFromUrl();
	});

	// Svelte 5 + TanStack Query v6: returns reactive object, not a store
	const products = createQuery(() => ({
		queryKey: ['products'] as const,
		queryFn: () => dataProvider.getProducts()
	}));

	// Fetch tracker data for price history sparklines
	const trackerData = createQuery(() => ({
		queryKey: ['tracker'] as const,
		queryFn: () => dataProvider.getTrackerData(),
		staleTime: 1000 * 60 * 60 // 1 hour
	}));

	// Create a map of product ID -> full price history (for sparklines and chart modal)
	const priceHistoryMap = $derived.by(() => {
		if (!trackerData.data?.history) return new Map<string, ProductPriceHistory>();

		const map = new Map<string, ProductPriceHistory>();
		for (const [productId, history] of Object.entries(trackerData.data.history)) {
			if (history.lowest && history.lowest.length >= 1) {
				map.set(productId, history);
			}
		}
		return map;
	});

	// Responsive columns based on window width (fewer columns when sidebar is shown)
	let windowWidth = $state(typeof window !== 'undefined' ? window.innerWidth : 1200);
	const showSidebar = $derived(windowWidth >= 1024); // lg breakpoint

	const columns = $derived(
		showSidebar
			? windowWidth >= 1536
				? 4
				: windowWidth >= 1280
					? 3
					: 2 // With sidebar
			: windowWidth >= 640
				? 2
				: 1 // Without sidebar (mobile)
	);

	function handleResize() {
		windowWidth = window.innerWidth;
	}

	// Extract categories and stores from products
	const categories = $derived(
		products.data?.products ? extractCategories(products.data.products) : []
	);
	const stores = $derived(products.data?.products ? extractStores(products.data.products) : []);

	// Filter products based on current filter state
	const filteredProducts = $derived(
		products.data?.products ? filterProducts(products.data.products, filters.value) : []
	);

	// Live region announcement for screen readers
	const filterAnnouncement = $derived(
		products.data
			? `Showing ${filteredProducts.length.toLocaleString()} of ${products.data.productCount.toLocaleString()} products`
			: ''
	);

	// Format full timestamp for tooltip
	function formatFullTimestamp(dateStr: string): string {
		return new Date(dateStr).toLocaleString('en-AU', {
			weekday: 'short',
			day: 'numeric',
			month: 'short',
			year: 'numeric',
			hour: 'numeric',
			minute: '2-digit',
			hour12: true
		});
	}

	// Format short timestamp for display
	function formatShortTimestamp(dateStr: string): string {
		return new Date(dateStr).toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		});
	}
</script>

<svelte:window onresize={handleResize} />

<svelte:head>
	<title>GSAU.gg - Gel Blaster Price Comparison</title>
	<meta
		name="description"
		content="Compare prices across 14+ Australian gel blaster retailers. Find the best deals on gel blasters, accessories, and more."
	/>
	<link rel="canonical" href="https://www.gsau.gg/" />
	<meta property="og:title" content="GSAU.gg - Gel Blaster Price Comparison" />
	<meta
		property="og:description"
		content="Compare prices across 14+ Australian gel blaster retailers. Find the best deals on gel blasters, accessories, and more."
	/>
	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://www.gsau.gg/" />
	{@html `<script type="application/ld+json">${JSON.stringify({
		'@context': 'https://schema.org',
		'@type': 'WebSite',
		name: 'GSAU.gg',
		description: 'Compare prices across 14+ Australian gel blaster retailers',
		url: 'https://www.gsau.gg/',
		potentialAction: {
			'@type': 'SearchAction',
			target: 'https://www.gsau.gg/?q={search_term_string}',
			'query-input': 'required name=search_term_string'
		}
	})}</script>`}
</svelte:head>

<!-- Live region for screen reader announcements -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
	{filterAnnouncement}
</div>

<div class="flex flex-col gap-4">
	{#if products.isLoading}
		<div class="space-y-3">
			<p class="text-sm text-muted-foreground">Loading products...</p>
			<Progress value={undefined} class="h-1 animate-pulse" />
		</div>
	{:else if products.isError}
		<Alert.Root variant="destructive" class="border-destructive/50 bg-destructive/10">
			<svg
				class="h-4 w-4"
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
				/>
			</svg>
			<Alert.Title>Error loading products</Alert.Title>
			<Alert.Description
				>{products.error?.message ?? 'Please try refreshing the page.'}</Alert.Description
			>
		</Alert.Root>
	{:else if products.data}
		<!-- Compact header with title, stats, and view toggle -->
		<div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
			<div class="flex items-baseline gap-4">
				<h1 class="text-xl sm:text-2xl font-bold tracking-tight">Products</h1>
				<p class="text-sm text-muted-foreground">
					<span class="font-mono font-semibold tabular-nums text-foreground"
						>{filteredProducts.length.toLocaleString()}</span
					>
					of
					<span class="font-mono font-semibold tabular-nums text-foreground"
						>{products.data.productCount.toLocaleString()}</span
					>
					products
					<span class="text-border">•</span>
					<span class="font-mono font-semibold tabular-nums text-foreground"
						>{products.data.storeCount}</span
					>
					stores
					<span class="hidden sm:inline">
						<span class="text-border">•</span>
						<Tooltip.Root>
							<Tooltip.Trigger class="cursor-default">
								Updated <span class="tabular-nums"
									>{formatShortTimestamp(products.data.lastUpdated)}</span
								>
							</Tooltip.Trigger>
							<Tooltip.Content>
								{formatFullTimestamp(products.data.lastUpdated)}
							</Tooltip.Content>
						</Tooltip.Root>
					</span>
				</p>
			</div>

			<div class="flex items-center gap-2">
				<!-- Sort dropdown -->
				<select
					value={filters.value.sortBy}
					onchange={(e) => filters.setSortBy(e.currentTarget.value as typeof filters.value.sortBy)}
					class="h-8 rounded-md border border-input bg-background px-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
					aria-label="Sort products"
				>
					<option value="discount-$">Best Deals ($)</option>
					<option value="discount-%">Best Deals (%)</option>
					<option value="price-asc">Price: Low → High</option>
					<option value="price-desc">Price: High → Low</option>
					<option value="name-asc">Name: A → Z</option>
					<option value="name-desc">Name: Z → A</option>
				</select>

				<!-- View toggle (mobile only) -->
				{#if !showSidebar}
					<div
						class="flex items-center gap-1 rounded-md border border-border p-0.5"
						role="group"
						aria-label="View mode"
					>
						<button
							type="button"
							onclick={() => viewMode.set('grid')}
							class="flex h-7 w-7 items-center justify-center rounded transition-colors {viewMode.value ===
							'grid'
								? 'bg-primary text-primary-foreground'
								: 'text-muted-foreground hover:bg-muted hover:text-foreground'}"
							aria-label="Grid view"
							aria-pressed={viewMode.value === 'grid'}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="16"
								height="16"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<rect width="7" height="7" x="3" y="3" rx="1" />
								<rect width="7" height="7" x="14" y="3" rx="1" />
								<rect width="7" height="7" x="14" y="14" rx="1" />
								<rect width="7" height="7" x="3" y="14" rx="1" />
							</svg>
						</button>
						<button
							type="button"
							onclick={() => viewMode.set('list')}
							class="flex h-7 w-7 items-center justify-center rounded transition-colors {viewMode.value ===
							'list'
								? 'bg-primary text-primary-foreground'
								: 'text-muted-foreground hover:bg-muted hover:text-foreground'}"
							aria-label="List view"
							aria-pressed={viewMode.value === 'list'}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="16"
								height="16"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<line x1="3" x2="21" y1="6" y2="6" />
								<line x1="3" x2="21" y1="12" y2="12" />
								<line x1="3" x2="21" y1="18" y2="18" />
							</svg>
						</button>
					</div>
				{/if}
			</div>
		</div>

		<!-- Main content with optional sidebar -->
		<div class="flex gap-6">
			<!-- Filter sidebar (desktop only) -->
			{#if showSidebar}
				<aside class="sticky top-16 w-64 shrink-0" aria-label="Filter products">
					<FilterPanel {categories} {stores} />
				</aside>
			{/if}

			<!-- Product grid/list section -->
			<section class="min-w-0 flex-1" aria-label="Product listings">
				<VirtualProductGrid
					products={filteredProducts}
					{columns}
					{priceHistoryMap}
					viewMode={showSidebar ? 'grid' : viewMode.value}
				/>
			</section>
		</div>

		<!-- Mobile filter sheet (shown via floating button) -->
		{#if !showSidebar}
			<FilterSheet {categories} {stores} productCount={filteredProducts.length} />
		{/if}
	{/if}
</div>
