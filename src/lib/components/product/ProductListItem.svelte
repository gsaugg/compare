<script lang="ts">
	import type { Product, Vendor, ProductPriceHistory } from '$lib/data/types';
	import { formatPrice, pricesEqual } from '$lib/utils/format';
	import { filters } from '$lib/stores/filters.svelte';
	import PriceHistoryModal from './PriceHistoryModal.svelte';
	import VendorButton from './VendorButton.svelte';
	import { Badge } from '$lib/components/ui/badge';

	interface Props {
		product: Product;
		priceHistory?: ProductPriceHistory;
	}

	let { product, priceHistory }: Props = $props();

	// Modal state
	let modalOpen = $state(false);

	// Filter and sort vendors by price, with in-stock first within same price
	// Uses stable alphabetical sort for same-price vendors (fair + no layout thrashing)
	const sortedVendors = $derived.by(() => {
		let vendors = [...product.vendors];
		if (filters.value.inStockOnly) {
			vendors = vendors.filter((v) => v.inStock);
		}

		// Sort by: price (ascending), in-stock first, then alphabetically by name
		return vendors.sort((a, b) => {
			// Primary: sort by price
			const priceDiff = a.price - b.price;
			if (Math.abs(priceDiff) >= 0.01) {
				return priceDiff;
			}

			// Secondary: in-stock vendors first
			if (a.inStock !== b.inStock) {
				return a.inStock ? -1 : 1;
			}

			// Tertiary: alphabetical by vendor name (stable, fair)
			return a.name.localeCompare(b.name);
		});
	});

	const lowestPrice = $derived(
		sortedVendors.length > 0 ? sortedVendors[0].price : product.lowestPrice
	);

	function isLowestPrice(vendor: Vendor): boolean {
		return pricesEqual(vendor.price, lowestPrice);
	}

	// Count total and in-stock vendors for display
	const totalVendors = $derived(product.vendors.length);
	const inStockVendors = $derived(product.vendors.filter((v) => v.inStock).length);

	// Fallback image on error
	let imageError = $state(false);
	const imageSrc = $derived(
		imageError || !product.image
			? 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="96" height="96" fill="%23ccc"%3E%3Crect width="96" height="96"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-size="12" fill="%23666"%3ENo Image%3C/text%3E%3C/svg%3E'
			: product.image
	);
</script>

<!-- List item container -->
<div class="flex w-full gap-3 rounded-lg border border-border bg-card p-3">
	<!-- Thumbnail - tapping opens price history modal -->
	<button
		type="button"
		onclick={() => (modalOpen = true)}
		class="relative h-24 w-24 shrink-0 cursor-pointer overflow-hidden rounded-md bg-muted transition-opacity hover:opacity-80"
		aria-label="View price history for {product.title}"
	>
		<img
			src={imageSrc}
			alt={product.title}
			class="h-full w-full object-contain p-1"
			loading="lazy"
			onerror={() => (imageError = true)}
		/>
		<!-- Out of stock overlay -->
		{#if !product.inStock}
			<div class="absolute inset-0 flex items-center justify-center bg-background/5">
				<Badge variant="destructive" class="text-xs">Out of Stock</Badge>
			</div>
		{/if}
	</button>

	<!-- Content -->
	<div class="flex min-w-0 flex-1 flex-col gap-2">
		<!-- Title - tapping opens price history modal -->
		<button
			type="button"
			onclick={() => (modalOpen = true)}
			class="text-left"
			aria-label="View price history for {product.title}"
		>
			<h3
				class="line-clamp-1 text-sm font-medium leading-tight text-foreground hover:text-primary transition-colors"
				title={product.title}
			>
				{product.title}
			</h3>
		</button>

		<!-- Price and store count -->
		<div class="flex items-baseline gap-2">
			<span class="text-base font-bold tabular-nums text-primary">{formatPrice(lowestPrice)}</span>
			<span class="text-xs tabular-nums text-muted-foreground">
				{totalVendors}
				{totalVendors === 1 ? 'store' : 'stores'} ({inStockVendors} in stock)
			</span>
		</div>

		<!-- All vendor buttons -->
		<div class="flex min-w-0 flex-col gap-1.5">
			{#each sortedVendors as vendor (vendor.name)}
				<VendorButton {vendor} isLowest={isLowestPrice(vendor)} />
			{/each}
		</div>
	</div>
</div>

<!-- Price history modal -->
{#if priceHistory}
	<PriceHistoryModal
		{product}
		history={priceHistory}
		bind:open={modalOpen}
		onOpenChange={(open) => (modalOpen = open)}
	/>
{/if}
