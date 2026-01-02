<script lang="ts">
	import type { Vendor } from '$lib/data/types';
	import {
		formatPrice,
		getDiscountPercent,
		addUtmParams,
		trackStoreClick
	} from '$lib/utils/format';

	interface Props {
		vendor: Vendor;
		isLowest: boolean;
		showDiscount?: boolean;
	}

	let { vendor, isLowest, showDiscount = true }: Props = $props();

	const discountPercent = $derived(getDiscountPercent(vendor.price, vendor.regularPrice));
	const vendorUrl = $derived(addUtmParams(vendor.url));

	// Accessible label for screen readers
	const ariaLabel = $derived(() => {
		let label = `Buy from ${vendor.name} for ${formatPrice(vendor.price)}`;
		if (isLowest) label += ', lowest price';
		if (!vendor.inStock) label += ', out of stock';
		if (discountPercent > 0) label += `, ${discountPercent}% off`;
		return label + '. Opens in new tab.';
	});
</script>

<a
	href={vendorUrl}
	target="_blank"
	rel="noopener noreferrer"
	onclick={() => trackStoreClick(vendor.name)}
	aria-label={ariaLabel()}
	class="group relative flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium transition-colors
		{isLowest
		? 'border-primary bg-primary text-primary-foreground hover:bg-primary/90'
		: 'border-border bg-background text-foreground hover:bg-muted'}"
>
	<!-- Stock indicator (visual only, info in aria-label) -->
	<span
		class="h-2.5 w-2.5 shrink-0 rounded-full ring-2 {vendor.inStock
			? 'bg-green-400 ring-white/80'
			: 'bg-red-500 ring-white/80'}"
		aria-hidden="true"
	></span>

	<!-- Vendor name -->
	<span class="truncate">{vendor.name}</span>

	<!-- Price -->
	<span class="ml-auto shrink-0 font-bold tabular-nums">{formatPrice(vendor.price)}</span>

	<!-- Discount badge -->
	{#if showDiscount && discountPercent > 0}
		<span
			class="absolute -right-2 -top-2 rounded-full bg-price-drop px-1.5 py-0.5 text-[10px] font-bold tabular-nums text-white"
		>
			-{discountPercent}%
		</span>
	{/if}
</a>
