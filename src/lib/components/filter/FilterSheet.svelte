<script lang="ts">
	import { Dialog } from 'bits-ui';
	import FilterPanel from './FilterPanel.svelte';
	import { filters } from '$lib/stores/filters.svelte';

	interface Props {
		categories: string[];
		stores: string[];
		productCount: number;
	}

	let { categories, stores, productCount }: Props = $props();

	let open = $state(false);

	// Count active filters for badge
	const activeFilterCount = $derived(
		(filters.value.search ? 1 : 0) +
			filters.value.categories.length +
			filters.value.stores.length +
			(filters.value.minPrice !== null ? 1 : 0) +
			(filters.value.maxPrice !== null ? 1 : 0) +
			(filters.value.inStockOnly ? 1 : 0) +
			(filters.value.onSaleOnly ? 1 : 0)
	);
</script>

<!-- Floating filter button (mobile only) -->
<button
	onclick={() => (open = true)}
	class="fixed bottom-20 right-4 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 active:scale-95 lg:hidden"
	aria-label="Open filters"
>
	<svg
		xmlns="http://www.w3.org/2000/svg"
		width="24"
		height="24"
		viewBox="0 0 24 24"
		fill="none"
		stroke="currentColor"
		stroke-width="2"
		stroke-linecap="round"
		stroke-linejoin="round"
	>
		<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
	</svg>
	{#if activeFilterCount > 0}
		<span
			class="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs font-medium text-white"
		>
			{activeFilterCount}
		</span>
	{/if}
</button>

<!-- Bottom sheet dialog -->
<Dialog.Root bind:open>
	<Dialog.Portal>
		<Dialog.Overlay
			class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
		/>
		<Dialog.Content
			class="fixed inset-x-0 bottom-0 z-50 flex max-h-[85vh] flex-col rounded-t-2xl border-t border-border bg-background shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom"
		>
			<!-- Handle bar -->
			<div class="flex justify-center py-3">
				<div class="h-1.5 w-12 rounded-full bg-muted-foreground/30"></div>
			</div>

			<!-- Header -->
			<div class="flex items-center justify-between border-b border-border px-4 pb-3">
				<Dialog.Title class="text-lg font-semibold">Filters</Dialog.Title>
				<Dialog.Close
					class="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="20"
						height="20"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<path d="M18 6 6 18" />
						<path d="m6 6 12 12" />
					</svg>
				</Dialog.Close>
			</div>

			<!-- Filter content (scrollable) -->
			<div class="flex-1 overflow-y-auto px-4 py-4">
				<FilterPanel {categories} {stores} showHeader={false} />
			</div>

			<!-- Footer with apply button -->
			<div class="border-t border-border p-4">
				<button
					onclick={() => (open = false)}
					class="w-full rounded-md bg-primary py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90"
				>
					Show {productCount.toLocaleString()} products
				</button>
			</div>
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>

<style>
	/* Animation keyframes for bottom sheet */
	:global([data-state='open'].animate-in) {
		animation: slide-in-from-bottom 0.3s ease-out;
	}

	:global([data-state='closed'].animate-out) {
		animation: slide-out-to-bottom 0.2s ease-in;
	}

	:global(.fade-in-0) {
		animation: fade-in 0.3s ease-out;
	}

	:global(.fade-out-0) {
		animation: fade-out 0.2s ease-in;
	}

	@keyframes slide-in-from-bottom {
		from {
			transform: translateY(100%);
		}
		to {
			transform: translateY(0);
		}
	}

	@keyframes slide-out-to-bottom {
		from {
			transform: translateY(0);
		}
		to {
			transform: translateY(100%);
		}
	}

	@keyframes fade-in {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	@keyframes fade-out {
		from {
			opacity: 1;
		}
		to {
			opacity: 0;
		}
	}
</style>
