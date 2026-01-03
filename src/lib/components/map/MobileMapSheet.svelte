<script lang="ts">
	import * as Sheet from '$lib/components/ui/sheet';
	import { Button } from '$lib/components/ui/button';
	import MapFilters from './MapFilters.svelte';
	import MapSidebar from './MapSidebar.svelte';
	import type { Location, LocationType, AustralianState } from '$lib/data/types';
	import List from '@lucide/svelte/icons/list';
	import Filter from '@lucide/svelte/icons/filter';

	interface Props {
		locations: Location[];
		filteredLocations: Location[];
		selectedTypes: LocationType[];
		selectedStates: AustralianState[];
		selectedLocation: Location | null;
		userLocation?: { lat: number; lng: number } | null;
		onTypesChange: (types: LocationType[]) => void;
		onStatesChange: (states: AustralianState[]) => void;
		onSelectLocation: (location: Location) => void;
	}

	let {
		locations,
		filteredLocations,
		selectedTypes,
		selectedStates,
		selectedLocation,
		userLocation = null,
		onTypesChange,
		onStatesChange,
		onSelectLocation
	}: Props = $props();

	let sheetOpen = $state(false);
	let activeTab = $state<'list' | 'filters'>('list');

	function handleSelectLocation(location: Location) {
		onSelectLocation(location);
		sheetOpen = false; // Close sheet when location is selected
	}
</script>

<!-- Floating button to open sheet -->
<div class="fixed bottom-20 left-4 z-[1000] lg:hidden">
	<Button
		variant="default"
		size="lg"
		class="shadow-lg"
		onclick={() => {
			sheetOpen = true;
			activeTab = 'list';
		}}
	>
		<List class="mr-2 h-5 w-5" />
		Locations ({filteredLocations.length})
	</Button>
</div>

<Sheet.Root bind:open={sheetOpen}>
	<Sheet.Content side="bottom" class="h-[70vh] max-h-[70vh] rounded-t-xl">
		<Sheet.Header class="border-b border-border pb-4">
			<div class="flex items-center gap-2">
				<Button
					variant={activeTab === 'list' ? 'default' : 'ghost'}
					size="sm"
					onclick={() => (activeTab = 'list')}
				>
					<List class="mr-1.5 h-4 w-4" />
					List
				</Button>
				<Button
					variant={activeTab === 'filters' ? 'default' : 'ghost'}
					size="sm"
					onclick={() => (activeTab = 'filters')}
				>
					<Filter class="mr-1.5 h-4 w-4" />
					Filters
					{#if selectedStates.length > 0 || selectedTypes.length < 2}
						<span
							class="ml-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary-foreground text-xs text-primary"
						>
							{selectedStates.length + (selectedTypes.length < 2 ? 1 : 0)}
						</span>
					{/if}
				</Button>
			</div>
		</Sheet.Header>

		<div class="h-full overflow-y-auto pb-safe pt-4">
			{#if activeTab === 'list'}
				<MapSidebar
					locations={filteredLocations}
					{selectedLocation}
					{userLocation}
					onSelectLocation={handleSelectLocation}
				/>
			{:else}
				<MapFilters {locations} {selectedTypes} {selectedStates} {onTypesChange} {onStatesChange} />
			{/if}
		</div>
	</Sheet.Content>
</Sheet.Root>
