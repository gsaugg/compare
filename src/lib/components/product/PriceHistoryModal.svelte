<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import type { Product, ProductPriceHistory } from '$lib/data/types';
	import { formatPrice, pricesEqual, addUtmParams, trackStoreClick } from '$lib/utils/format';
	import PriceHistoryChart from './PriceHistoryChart.svelte';

	interface Props {
		product: Product;
		history: ProductPriceHistory;
		open: boolean;
		onOpenChange: (open: boolean) => void;
	}

	let { product, history, open = $bindable(), onOpenChange }: Props = $props();

	// Calculate price stats from all vendors with vendor info
	const priceStats = $derived.by(() => {
		// Track all prices with vendor info
		const allPricesWithVendor: Array<{ price: number; vendor: string }> = [];

		for (const [vendor, points] of Object.entries(history.vendors)) {
			for (const point of points) {
				allPricesWithVendor.push({ price: point.p, vendor });
			}
		}

		if (allPricesWithVendor.length === 0) return null;

		// Find 30-day low and high with vendor names
		const sortedByPrice = [...allPricesWithVendor].sort((a, b) => a.price - b.price);
		const lowestEntry = sortedByPrice[0];
		const highestEntry = sortedByPrice[sortedByPrice.length - 1];

		// Current lowest price vendor (from product.vendors, sorted by price)
		const currentVendor = [...product.vendors].sort((a, b) => a.price - b.price)[0];
		const currentPrice = currentVendor?.price ?? lowestEntry.price;

		// Calculate if current is at historical low
		const isAtLow = pricesEqual(currentPrice, lowestEntry.price);

		// Calculate % above lowest
		const percentAboveLow =
			lowestEntry.price > 0 ? ((currentPrice - lowestEntry.price) / lowestEntry.price) * 100 : 0;

		return {
			current: currentPrice,
			currentVendor: currentVendor?.name,
			currentUrl: currentVendor?.url,
			lowest: lowestEntry.price,
			lowestVendor: lowestEntry.vendor,
			highest: highestEntry.price,
			highestVendor: highestEntry.vendor,
			isAtLow,
			percentAboveLow
		};
	});

	// Get vendor URL from product.vendors by name
	function getVendorUrl(vendorName: string): string | undefined {
		return product.vendors.find((v) => v.name === vendorName)?.url;
	}
</script>

<Dialog.Root bind:open {onOpenChange}>
	<Dialog.Content class="max-h-[90vh] w-[95vw] max-w-4xl overflow-hidden">
		<!-- Header -->
		<div class="border-b border-border px-4 py-3">
			<Dialog.Title class="text-lg font-semibold leading-tight">
				{product.title}
			</Dialog.Title>
			<Dialog.Description class="mt-0.5 text-sm text-muted-foreground">
				30-day price history across {Object.keys(history.vendors).length} vendor{Object.keys(
					history.vendors
				).length !== 1
					? 's'
					: ''}
			</Dialog.Description>
		</div>

		<!-- Price stats -->
		{#if priceStats}
			<div class="grid grid-cols-3 gap-2 border-b border-border px-4 py-3">
				<!-- Current price -->
				<Card.Root class="gap-0 py-2 shadow-none bg-muted/30 border-0">
					<Card.Content class="px-3">
						<p class="text-xs text-muted-foreground">Current</p>
						<p class="text-base font-bold tabular-nums">{formatPrice(priceStats.current)}</p>
						{#if priceStats.currentVendor && priceStats.currentUrl}
							<a
								href={addUtmParams(priceStats.currentUrl)}
								target="_blank"
								rel="noopener noreferrer"
								onclick={() => trackStoreClick(priceStats.currentVendor!)}
								class="text-xs text-primary hover:underline"
							>
								{priceStats.currentVendor} →
							</a>
						{:else if priceStats.currentVendor}
							<p class="text-xs text-muted-foreground">{priceStats.currentVendor}</p>
						{/if}
						{#if priceStats.isAtLow}
							<Badge variant="default" class="mt-0.5 bg-price-drop text-white text-xs px-1.5 py-0"
								>Lowest!</Badge
							>
						{:else if priceStats.percentAboveLow > 0}
							<p class="text-xs text-muted-foreground">
								{priceStats.percentAboveLow.toFixed(0)}% above low
							</p>
						{/if}
					</Card.Content>
				</Card.Root>
				<!-- 30-day low -->
				<Card.Root class="gap-0 py-2 shadow-none bg-muted/30 border-0">
					<Card.Content class="px-3">
						<p class="text-xs text-muted-foreground">30-day Low</p>
						<p class="text-base font-bold tabular-nums text-price-drop">
							{formatPrice(priceStats.lowest)}
						</p>
						{#if priceStats.lowestVendor}
							{@const vendorUrl = getVendorUrl(priceStats.lowestVendor)}
							{#if vendorUrl}
								<a
									href={addUtmParams(vendorUrl)}
									target="_blank"
									rel="noopener noreferrer"
									onclick={() => trackStoreClick(priceStats.lowestVendor!)}
									class="text-xs text-primary hover:underline"
								>
									{priceStats.lowestVendor} →
								</a>
							{:else}
								<p class="text-xs text-muted-foreground">{priceStats.lowestVendor}</p>
							{/if}
						{/if}
					</Card.Content>
				</Card.Root>
				<!-- 30-day high -->
				<Card.Root class="gap-0 py-2 shadow-none bg-muted/30 border-0">
					<Card.Content class="px-3">
						<p class="text-xs text-muted-foreground">30-day High</p>
						<p class="text-base font-bold tabular-nums text-price-rise">
							{formatPrice(priceStats.highest)}
						</p>
						{#if priceStats.highestVendor}
							{@const vendorUrl = getVendorUrl(priceStats.highestVendor)}
							{#if vendorUrl}
								<a
									href={addUtmParams(vendorUrl)}
									target="_blank"
									rel="noopener noreferrer"
									onclick={() => trackStoreClick(priceStats.highestVendor!)}
									class="text-xs text-primary hover:underline"
								>
									{priceStats.highestVendor} →
								</a>
							{:else}
								<p class="text-xs text-muted-foreground">{priceStats.highestVendor}</p>
							{/if}
						{/if}
					</Card.Content>
				</Card.Root>
			</div>
		{/if}

		<!-- Chart -->
		<div class="max-h-[60vh] overflow-y-auto scrollbar-none p-4">
			<PriceHistoryChart {history} productTitle={product.title} />
		</div>
	</Dialog.Content>
</Dialog.Root>
