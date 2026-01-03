<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import type { Location } from '$lib/data/types';
	import { calculateDistance, formatDistance } from './distance';

	interface Props {
		locations: Location[];
		selectedLocation: Location | null;
		onSelectLocation: (location: Location) => void;
		userLocation?: { lat: number; lng: number } | null;
	}

	let { locations, selectedLocation, onSelectLocation, userLocation = null }: Props = $props();

	// Calculate distance for a location
	function getDistance(location: Location): string | null {
		if (!userLocation) return null;
		const dist = calculateDistance(
			userLocation.lat,
			userLocation.lng,
			location.coordinates.lat,
			location.coordinates.lng
		);
		return formatDistance(dist);
	}
</script>

<div class="flex flex-col gap-1">
	{#if locations.length === 0}
		<div class="flex flex-col items-center gap-2 py-8 text-center text-muted-foreground">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="32"
				height="32"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="1.5"
				stroke-linecap="round"
				stroke-linejoin="round"
				class="opacity-50"
			>
				<circle cx="12" cy="10" r="3" />
				<path
					d="M12 2a8 8 0 0 0-8 8c0 1.892.402 3.13 1.5 4.5L12 22l6.5-7.5c1.098-1.37 1.5-2.608 1.5-4.5a8 8 0 0 0-8-8Z"
				/>
			</svg>
			<p class="text-sm">No locations match your filters</p>
			<p class="text-xs">Try adjusting your type or state filters</p>
		</div>
	{:else}
		{#each locations as location (location.id)}
			{@const distance = getDistance(location)}
			<button
				class="flex w-full items-center gap-3 rounded-md border border-transparent px-3 py-2 text-left transition-colors hover:bg-muted/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary
					{selectedLocation?.id === location.id ? 'border-primary bg-primary/5' : ''}"
				onclick={() => onSelectLocation(location)}
			>
				<!-- Type indicator -->
				<div class="flex shrink-0 gap-0.5">
					{#if location.types.includes('store')}
						<span
							class="h-2.5 w-2.5 rounded-full"
							style="background-color: var(--primary)"
							title="Store"
						></span>
					{/if}
					{#if location.types.includes('field')}
						<span
							class="h-2.5 w-2.5 rounded-full"
							style="background-color: var(--stock-available)"
							title="Field"
						></span>
					{/if}
				</div>

				<!-- Location info -->
				<div class="min-w-0 flex-1">
					<div class="text-sm font-medium">{location.name}</div>
					<div class="flex items-center gap-1.5 text-xs text-muted-foreground">
						<span>{location.state}</span>
						{#if distance}
							<span class="text-muted-foreground/60">•</span>
							<span class="text-primary">{distance}</span>
						{/if}
					</div>
				</div>

				<!-- Type badges (compact) -->
				<div class="flex shrink-0 gap-1">
					{#if location.types.includes('store') && location.types.includes('field')}
						<Badge variant="secondary" class="px-1.5 py-0 text-[10px]">Both</Badge>
					{/if}
				</div>
			</button>
		{/each}
	{/if}
</div>
