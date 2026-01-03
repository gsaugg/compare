<script lang="ts">
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { Button } from '$lib/components/ui/button';
	import type { Location, LocationType, AustralianState } from '$lib/data/types';

	interface Props {
		locations: Location[];
		selectedTypes: LocationType[];
		selectedStates: AustralianState[];
		onTypesChange: (types: LocationType[]) => void;
		onStatesChange: (states: AustralianState[]) => void;
	}

	let { locations, selectedTypes, selectedStates, onTypesChange, onStatesChange }: Props = $props();

	// Count locations by type
	const typeCounts = $derived({
		store: locations.filter((l) => l.types.includes('store')).length,
		field: locations.filter((l) => l.types.includes('field')).length
	});

	// Count locations by state
	const stateCounts = $derived(
		locations.reduce(
			(acc, loc) => {
				acc[loc.state] = (acc[loc.state] || 0) + 1;
				return acc;
			},
			{} as Record<AustralianState, number>
		)
	);

	// Available states (only show states with locations)
	const availableStates = $derived(
		(Object.keys(stateCounts) as AustralianState[]).sort((a, b) => {
			// Sort by count descending, then alphabetically
			const countDiff = (stateCounts[b] || 0) - (stateCounts[a] || 0);
			return countDiff !== 0 ? countDiff : a.localeCompare(b);
		})
	);

	function toggleType(type: LocationType) {
		if (selectedTypes.includes(type)) {
			// Don't allow deselecting all types
			if (selectedTypes.length > 1) {
				onTypesChange(selectedTypes.filter((t) => t !== type));
			}
		} else {
			onTypesChange([...selectedTypes, type]);
		}
	}

	function toggleState(state: AustralianState) {
		if (selectedStates.includes(state)) {
			onStatesChange(selectedStates.filter((s) => s !== state));
		} else {
			onStatesChange([...selectedStates, state]);
		}
	}

	function clearStates() {
		onStatesChange([]);
	}
</script>

<div class="space-y-4">
	<!-- Type filters -->
	<div>
		<h3 class="mb-2 text-sm font-medium">Type</h3>
		<div class="flex flex-col gap-2">
			<label for="filter-store" class="flex cursor-pointer items-center gap-2">
				<Checkbox
					id="filter-store"
					checked={selectedTypes.includes('store')}
					onCheckedChange={() => toggleType('store')}
				/>
				<span class="flex items-center gap-2">
					<span class="inline-block h-3 w-3 rounded-full" style="background-color: var(--primary)"
					></span>
					<span>Stores</span>
					<span class="text-muted-foreground">({typeCounts.store})</span>
				</span>
			</label>
			<label for="filter-field" class="flex cursor-pointer items-center gap-2">
				<Checkbox
					id="filter-field"
					checked={selectedTypes.includes('field')}
					onCheckedChange={() => toggleType('field')}
				/>
				<span class="flex items-center gap-2">
					<span
						class="inline-block h-3 w-3 rounded-full"
						style="background-color: var(--stock-available)"
					></span>
					<span>Fields</span>
					<span class="text-muted-foreground">({typeCounts.field})</span>
				</span>
			</label>
		</div>
	</div>

	<!-- State filters -->
	{#if availableStates.length > 0}
		<div>
			<div class="mb-2 flex items-center justify-between">
				<h3 class="text-sm font-medium">State</h3>
				{#if selectedStates.length > 0}
					<Button variant="ghost" size="sm" class="h-auto px-2 py-1 text-xs" onclick={clearStates}>
						Clear
					</Button>
				{/if}
			</div>
			<div class="flex flex-wrap gap-1.5">
				{#each availableStates as state}
					<Button
						variant={selectedStates.includes(state) ? 'default' : 'outline'}
						size="sm"
						class="h-7 px-2 text-xs"
						onclick={() => toggleState(state)}
					>
						{state}
						<span class="ml-1 text-xs opacity-70">({stateCounts[state]})</span>
					</Button>
				{/each}
			</div>
		</div>
	{/if}
</div>
