<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import type { Location } from '$lib/data/types';
	import { getLocationTypeLabel } from './markers';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import MapPin from '@lucide/svelte/icons/map-pin';
	import ShoppingBag from '@lucide/svelte/icons/shopping-bag';
	import X from '@lucide/svelte/icons/x';

	interface Props {
		location: Location;
		storeName?: string; // Store name from stores.json for "View Products" link
		onClose?: () => void;
		class?: string;
	}

	let { location, storeName, onClose, class: className = '' }: Props = $props();

	const typeLabel = $derived(getLocationTypeLabel(location.types));
	const isStore = $derived(location.types.includes('store'));
	const isField = $derived(location.types.includes('field'));
</script>

<div
	class="animate-in fade-in slide-in-from-bottom-2 duration-200 rounded-lg border border-border bg-card p-4 shadow-lg {className}"
>
	<!-- Header -->
	<div class="mb-3 flex items-start justify-between gap-2">
		<div class="min-w-0 flex-1">
			<h3 class="text-base font-semibold">{location.name}</h3>
			<div class="mt-1 flex flex-wrap gap-1">
				{#if isStore}
					<Badge variant="outline" class="border-primary/50 bg-primary/10 text-primary">
						Store
					</Badge>
				{/if}
				{#if isField}
					<Badge
						variant="outline"
						class="border-stock-available/50 bg-stock-available/10 text-stock-available"
					>
						Field
					</Badge>
				{/if}
				<Badge variant="secondary" class="text-xs">{location.state}</Badge>
			</div>
		</div>
		{#if onClose}
			<Button variant="ghost" size="icon" class="h-7 w-7 shrink-0" onclick={onClose}>
				<X class="h-4 w-4" />
			</Button>
		{/if}
	</div>

	<!-- Actions -->
	<div class="flex flex-col gap-2">
		{#if location.website}
			<Button
				variant="outline"
				size="sm"
				class="w-full justify-start"
				href={location.website}
				target="_blank"
				rel="noopener noreferrer"
			>
				<ExternalLink class="mr-2 h-4 w-4" />
				{location.fieldWebsite ? 'Store Website' : 'Visit Website'}
			</Button>
		{/if}

		{#if location.fieldWebsite}
			<Button
				variant="outline"
				size="sm"
				class="w-full justify-start"
				href={location.fieldWebsite}
				target="_blank"
				rel="noopener noreferrer"
			>
				<ExternalLink class="mr-2 h-4 w-4" />
				Field Website
			</Button>
		{/if}

		{#if location.googleMapsUrl}
			<Button
				variant="outline"
				size="sm"
				class="w-full justify-start"
				href={location.googleMapsUrl}
				target="_blank"
				rel="noopener noreferrer"
			>
				<MapPin class="mr-2 h-4 w-4" />
				Open in Google Maps
			</Button>
		{/if}

		{#if location.storeId && storeName}
			<Button
				variant="default"
				size="sm"
				class="w-full justify-start"
				href="/?store={encodeURIComponent(storeName)}"
			>
				<ShoppingBag class="mr-2 h-4 w-4" />
				View Products
			</Button>
		{/if}
	</div>
</div>
