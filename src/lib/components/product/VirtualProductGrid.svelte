<script lang="ts">
	import type { Product, ProductPriceHistory } from '$lib/data/types';
	import type { ViewMode } from '$lib/stores/viewMode.svelte';
	import ProductCard from './ProductCard.svelte';
	import ProductListItem from './ProductListItem.svelte';
	import { browser } from '$app/environment';

	interface Props {
		products: Product[];
		columns?: number;
		priceHistoryMap?: Map<string, ProductPriceHistory>;
		viewMode?: ViewMode;
	}

	let { products, columns = 4, priceHistoryMap, viewMode = 'grid' }: Props = $props();

	// Pagination - show 50 products at a time
	const PAGE_SIZE = 50;
	let visibleCount = $state(PAGE_SIZE);

	// Reset visible count when products change
	$effect(() => {
		// Depend on products array
		const _ = products.length;
		visibleCount = PAGE_SIZE;
	});

	const visibleProducts = $derived(products.slice(0, visibleCount));
	const hasMore = $derived(visibleCount < products.length);

	function loadMore() {
		visibleCount = Math.min(visibleCount + PAGE_SIZE, products.length);
	}

	// Infinite scroll - load more when sentinel enters viewport
	function infiniteScroll(node: HTMLElement) {
		if (!browser) return;

		const observer = new IntersectionObserver(
			(entries) => {
				if (entries[0].isIntersecting && hasMore) {
					loadMore();
				}
			},
			{ rootMargin: '200px' }
		);

		observer.observe(node);

		return {
			destroy() {
				observer.disconnect();
			}
		};
	}
</script>

<!-- Grid view -->
{#if viewMode === 'grid'}
	<div class="grid gap-4 pb-24" style="grid-template-columns: repeat({columns}, minmax(0, 1fr));">
		{#each visibleProducts as product (product.id)}
			<ProductCard {product} priceHistory={priceHistoryMap?.get(product.id)} />
		{/each}
	</div>
{:else}
	<!-- List view -->
	<div class="flex flex-col gap-3 pb-24">
		{#each visibleProducts as product (product.id)}
			<ProductListItem {product} priceHistory={priceHistoryMap?.get(product.id)} />
		{/each}
	</div>
{/if}

<!-- Sentinel element for infinite scroll -->
{#if hasMore}
	<div use:infiniteScroll class="h-4"></div>
{/if}
