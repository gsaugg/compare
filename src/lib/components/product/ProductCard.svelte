<script lang="ts">
	import type { Product, Vendor, ProductPriceHistory } from '$lib/data/types';
	import { formatPrice, pricesEqual } from '$lib/utils/format';
	import { filters } from '$lib/stores/filters.svelte';
	import VendorButton from './VendorButton.svelte';
	import PriceSparkline from './PriceSparkline.svelte';
	import PriceHistoryModal from './PriceHistoryModal.svelte';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import * as Tooltip from '$lib/components/ui/tooltip';

	interface Props {
		product: Product;
		priceHistory?: ProductPriceHistory;
	}

	let { product, priceHistory }: Props = $props();

	// Extract lowest price history for sparkline
	const sparklineData = $derived(priceHistory?.lowest ?? []);

	// Modal state
	let modalOpen = $state(false);

	// Filter and sort vendors by price, with in-stock first within same price
	// Uses stable alphabetical sort for same-price vendors (fair + no layout thrashing)
	const sortedVendors = $derived.by(() => {
		// Filter by in-stock if filter is active
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

	// Count total and in-stock vendors for display
	const totalVendors = $derived(product.vendors.length);
	const inStockVendors = $derived(product.vendors.filter((v) => v.inStock).length);

	function isLowestPrice(vendor: Vendor): boolean {
		return pricesEqual(vendor.price, lowestPrice);
	}

	// Fallback image on error
	let imageError = $state(false);
	const imageSrc = $derived(
		imageError || !product.image
			? 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200" fill="%23ccc"%3E%3Crect width="200" height="200"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-size="14" fill="%23666"%3ENo Image%3C/text%3E%3C/svg%3E'
			: product.image
	);
</script>

<Card.Root class="group gap-0 overflow-hidden p-0 transition-shadow hover:shadow-md">
	<!-- Image -->
	<div class="relative aspect-[3/2] sm:aspect-[4/3] overflow-hidden bg-muted">
		<img
			src={imageSrc}
			alt={product.title}
			class="h-full w-full object-contain p-2 transition-transform group-hover:scale-105"
			loading="lazy"
			onerror={() => (imageError = true)}
		/>

		<!-- Category badge -->
		{#if product.category}
			<Badge
				variant="secondary"
				class="absolute left-2 top-2 z-10 bg-background/80 backdrop-blur-sm"
			>
				{product.category}
			</Badge>
		{/if}

		<!-- Out of stock overlay -->
		{#if !product.inStock}
			<div class="absolute inset-0 flex items-center justify-center bg-background/5">
				<Badge variant="destructive" class="text-sm">Out of Stock</Badge>
			</div>
		{/if}
	</div>

	<!-- Content - grid layout for consistent alignment across cards -->
	<Card.Content class="grid grid-rows-[2.25rem_auto_1fr] gap-2 p-4">
		<!-- Title - fixed height for 2 lines to align content across cards -->
		<h3
			class="line-clamp-2 text-sm font-medium leading-tight text-foreground"
			title={product.title}
		>
			{product.title}
		</h3>

		<!-- Price summary with sparkline -->
		<div class="flex items-center justify-between gap-2">
			<div class="flex items-baseline gap-2">
				<span class="text-lg font-bold tabular-nums text-primary">{formatPrice(lowestPrice)}</span>
				<span class="text-xs tabular-nums text-muted-foreground">
					{totalVendors}
					{totalVendors === 1 ? 'store' : 'stores'} ({inStockVendors} in stock)
				</span>
			</div>
			{#if sparklineData.length >= 1}
				<Tooltip.Root>
					<Tooltip.Trigger>
						{#snippet child({ props })}
							<button
								{...props}
								type="button"
								onclick={() => (modalOpen = true)}
								aria-label="View price history"
								class="rounded p-1 hover:bg-muted transition-colors"
							>
								<PriceSparkline history={sparklineData} width={60} height={28} />
							</button>
						{/snippet}
					</Tooltip.Trigger>
					<Tooltip.Content>Click for price history</Tooltip.Content>
				</Tooltip.Root>
			{/if}
		</div>

		<!-- Vendor buttons -->
		<div class="flex flex-col gap-2">
			{#each sortedVendors as vendor (vendor.name)}
				<VendorButton {vendor} isLowest={isLowestPrice(vendor)} />
			{/each}
		</div>
	</Card.Content>
</Card.Root>

<!-- Price history modal -->
{#if priceHistory}
	<PriceHistoryModal
		{product}
		history={priceHistory}
		bind:open={modalOpen}
		onOpenChange={(open) => (modalOpen = open)}
	/>
{/if}
