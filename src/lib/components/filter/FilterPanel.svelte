<script lang="ts">
	import { filters, type FilterState } from '$lib/stores/filters.svelte';
	import { formatPrice } from '$lib/utils/format';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import * as Collapsible from '$lib/components/ui/collapsible';
	import { Separator } from '$lib/components/ui/separator';

	interface Props {
		categories: string[];
		stores: string[];
		showHeader?: boolean;
	}

	let { categories, stores, showHeader = true }: Props = $props();

	// Collapsible state (collapsed by default)
	let categoriesOpen = $state(false);
	let storesOpen = $state(false);

	// Local state for price inputs (to avoid updating URL on every keystroke)
	let minPriceInput = $state(filters.value.minPrice?.toString() ?? '');
	let maxPriceInput = $state(filters.value.maxPrice?.toString() ?? '');
	let priceDebounceTimer: ReturnType<typeof setTimeout> | null = null;

	// Apply price filter
	function applyPriceFilter() {
		if (priceDebounceTimer) clearTimeout(priceDebounceTimer);
		const min = minPriceInput ? Number(minPriceInput) : null;
		const max = maxPriceInput ? Number(maxPriceInput) : null;
		filters.setPriceRange(min, max);
	}

	// Debounced price filter (300ms delay)
	function debouncedPriceFilter() {
		if (priceDebounceTimer) clearTimeout(priceDebounceTimer);
		priceDebounceTimer = setTimeout(applyPriceFilter, 300);
	}

	// Cleanup timer on destroy
	$effect(() => {
		return () => {
			if (priceDebounceTimer) clearTimeout(priceDebounceTimer);
		};
	});

	// Clear all filters
	function clearFilters() {
		filters.reset();
		minPriceInput = '';
		maxPriceInput = '';
	}

	// Check if any filters are active
	const hasActiveFilters = $derived(
		filters.value.search !== '' ||
			filters.value.categories.length > 0 ||
			filters.value.stores.length > 0 ||
			filters.value.minPrice !== null ||
			filters.value.maxPrice !== null ||
			filters.value.inStockOnly ||
			filters.value.onSaleOnly
	);
</script>

<aside class="space-y-6">
	<!-- Filter header (optional) -->
	{#if showHeader}
		<div class="flex items-center justify-between">
			<h2 class="text-lg font-semibold">Filters</h2>
			{#if hasActiveFilters}
				<Button variant="link" size="sm" onclick={clearFilters}>Clear all</Button>
			{/if}
		</div>
	{:else if hasActiveFilters}
		<div class="flex justify-end">
			<Button variant="link" size="sm" onclick={clearFilters}>Clear all</Button>
		</div>
	{/if}

	<!-- Quick filters -->
	<div class="space-y-2">
		<h3 class="text-sm font-medium text-muted-foreground">Quick Filters</h3>
		<div class="flex flex-wrap gap-2">
			<button
				onclick={() => filters.setOnSaleOnly(!filters.value.onSaleOnly)}
				class="rounded-full px-3 py-1 text-sm font-medium transition-colors
					{filters.value.onSaleOnly
					? 'bg-primary text-primary-foreground'
					: 'bg-muted text-muted-foreground hover:bg-muted/80'}"
			>
				On Sale
			</button>
			<button
				onclick={() => filters.setInStockOnly(!filters.value.inStockOnly)}
				class="rounded-full px-3 py-1 text-sm font-medium transition-colors
					{filters.value.inStockOnly
					? 'bg-primary text-primary-foreground'
					: 'bg-muted text-muted-foreground hover:bg-muted/80'}"
			>
				In Stock
			</button>
		</div>
	</div>

	<Separator />

	<!-- Price range -->
	<div class="space-y-2">
		<h3 id="price-range-label" class="text-sm font-medium text-muted-foreground">Price Range</h3>
		<div class="flex items-center gap-2" role="group" aria-labelledby="price-range-label">
			<Input
				id="price-min"
				name="price-min"
				type="number"
				placeholder="Min"
				aria-label="Minimum price"
				bind:value={minPriceInput}
				oninput={debouncedPriceFilter}
				onblur={applyPriceFilter}
				onkeydown={(e) => e.key === 'Enter' && applyPriceFilter()}
			/>
			<span class="text-muted-foreground" aria-hidden="true">-</span>
			<Input
				id="price-max"
				name="price-max"
				type="number"
				placeholder="Max"
				aria-label="Maximum price"
				bind:value={maxPriceInput}
				oninput={debouncedPriceFilter}
				onblur={applyPriceFilter}
				onkeydown={(e) => e.key === 'Enter' && applyPriceFilter()}
			/>
		</div>
	</div>

	<Separator />

	<!-- Categories -->
	<Collapsible.Root bind:open={categoriesOpen} class="space-y-2">
		<Collapsible.Trigger
			class="flex w-full items-center justify-between text-sm font-medium text-muted-foreground hover:text-foreground"
		>
			<span class="flex items-center gap-2">
				Categories
				{#if filters.value.categories.length > 0}
					<span class="rounded-full bg-primary px-1.5 py-0.5 text-xs text-primary-foreground">
						{filters.value.categories.length}
					</span>
				{/if}
			</span>
			<svg
				class="h-4 w-4 transition-transform {categoriesOpen ? 'rotate-180' : ''}"
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path d="m6 9 6 6 6-6" />
			</svg>
		</Collapsible.Trigger>
		<Collapsible.Content>
			<div class="max-h-48 space-y-1 overflow-y-auto scrollbar-none">
				{#each categories as category}
					<label
						class="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted"
					>
						<Checkbox
							checked={filters.value.categories.includes(category)}
							onCheckedChange={() => filters.toggleCategory(category)}
						/>
						<span class="text-sm">{category}</span>
					</label>
				{/each}
			</div>
		</Collapsible.Content>
	</Collapsible.Root>

	<Separator />

	<!-- Stores -->
	<Collapsible.Root bind:open={storesOpen} class="space-y-2">
		<Collapsible.Trigger
			class="flex w-full items-center justify-between text-sm font-medium text-muted-foreground hover:text-foreground"
		>
			<span class="flex items-center gap-2">
				Stores
				{#if filters.value.stores.length > 0}
					<span class="rounded-full bg-primary px-1.5 py-0.5 text-xs text-primary-foreground">
						{filters.value.stores.length}
					</span>
				{/if}
			</span>
			<svg
				class="h-4 w-4 transition-transform {storesOpen ? 'rotate-180' : ''}"
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path d="m6 9 6 6 6-6" />
			</svg>
		</Collapsible.Trigger>
		<Collapsible.Content>
			<div class="max-h-48 space-y-1 overflow-y-auto scrollbar-none">
				{#each stores as store}
					<label
						class="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted"
					>
						<Checkbox
							checked={filters.value.stores.includes(store)}
							onCheckedChange={() => filters.toggleStore(store)}
						/>
						<span class="text-sm">{store}</span>
					</label>
				{/each}
			</div>
		</Collapsible.Content>
	</Collapsible.Root>

	<Separator />

	<!-- Discord link - more prominent -->
	<a
		href="https://discord.gg/rmfZtWD95f"
		target="_blank"
		rel="noopener"
		class="flex w-full items-center justify-center gap-2 rounded-md bg-[#5865F2] px-3 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#4752C4]"
	>
		<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
			<path
				d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"
			/>
		</svg>
		Join Gelsoft AU Discord
	</a>
</aside>
