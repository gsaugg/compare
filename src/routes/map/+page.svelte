<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import { dataProvider } from '$lib/data/static';
	import type { Location, LocationType, AustralianState } from '$lib/data/types';
	import type { Map as LeafletMap } from 'leaflet';
	import LeafletMapComponent from '$lib/components/map/LeafletMap.svelte';
	import MapFilters from '$lib/components/map/MapFilters.svelte';
	import MapSidebar from '$lib/components/map/MapSidebar.svelte';
	import MapMarkers from '$lib/components/map/MapMarkers.svelte';
	import LocationDetail from '$lib/components/map/LocationDetail.svelte';
	import MobileMapSheet from '$lib/components/map/MobileMapSheet.svelte';
	import UserLocationMarker from '$lib/components/map/UserLocationMarker.svelte';
	import * as Alert from '$lib/components/ui/alert';
	import { Button } from '$lib/components/ui/button';
	import Spinner from '$lib/components/ui/spinner.svelte';
	import { browser } from '$app/environment';
	import { page } from '$app/stores';
	import { replaceState } from '$app/navigation';
	import { calculateDistance } from '$lib/components/map/distance';
	import storesConfig from '../../../stores.json';

	// Build store name lookup from stores.json (single source of truth)
	const storeNames: Record<string, string> = Object.fromEntries(
		storesConfig.stores.map((store: { id: string; name: string }) => [store.id, store.name])
	);

	// Fetch locations data
	const locations = createQuery(() => ({
		queryKey: ['locations'] as const,
		queryFn: () => dataProvider.getLocations(),
		staleTime: 1000 * 60 * 60 // 1 hour
	}));

	// Map instance
	let map: LeafletMap | null = $state(null);

	// Filter state
	let selectedTypes = $state<LocationType[]>(['store', 'field']);
	let selectedStates = $state<AustralianState[]>([]);
	let selectedLocation = $state<Location | null>(null);

	// User location state
	let userLocation = $state<{ lat: number; lng: number } | null>(null);
	let locatingUser = $state(false);
	let locationError = $state<string | null>(null);
	let errorTimeoutId: ReturnType<typeof setTimeout> | null = null;

	// Request user location
	function locateUser() {
		if (!browser || !navigator.geolocation) {
			locationError = 'Geolocation is not supported by your browser';
			return;
		}

		locatingUser = true;
		locationError = null;

		navigator.geolocation.getCurrentPosition(
			(position) => {
				userLocation = {
					lat: position.coords.latitude,
					lng: position.coords.longitude
				};
				locatingUser = false;

				// Center map on user location with reasonable zoom
				if (map) {
					map.setView([userLocation.lat, userLocation.lng], 10);
				}
			},
			(error) => {
				locatingUser = false;
				switch (error.code) {
					case error.PERMISSION_DENIED:
						locationError = 'Location permission denied';
						break;
					case error.POSITION_UNAVAILABLE:
						locationError = 'Location unavailable';
						break;
					case error.TIMEOUT:
						locationError = 'Location request timed out';
						break;
					default:
						locationError = 'Unable to get location';
				}
				// Clear any existing timeout to avoid dismissing new errors
				if (errorTimeoutId) {
					clearTimeout(errorTimeoutId);
				}
				// Auto-dismiss error after 4 seconds
				errorTimeoutId = setTimeout(() => {
					locationError = null;
					errorTimeoutId = null;
				}, 4000);
			},
			{
				enableHighAccuracy: false,
				timeout: 10000,
				maximumAge: 300000 // 5 minutes
			}
		);
	}

	// Auto-fetch location if permission already granted
	$effect(() => {
		if (!browser || !navigator.permissions) return;

		navigator.permissions.query({ name: 'geolocation' }).then((result) => {
			if (result.state === 'granted') {
				locateUser();
			}
		});
	});

	// Initialize from URL params
	$effect(() => {
		if (!browser) return;
		const url = $page.url;

		// Parse type filter
		const typeParam = url.searchParams.get('type');
		if (typeParam) {
			const types = typeParam
				.split(',')
				.filter((t) => t === 'store' || t === 'field') as LocationType[];
			if (types.length > 0) {
				selectedTypes = types;
			}
		}

		// Parse state filter
		const stateParam = url.searchParams.get('state');
		if (stateParam) {
			const states = stateParam
				.split(',')
				.filter((s) =>
					['NSW', 'QLD', 'VIC', 'SA', 'WA', 'TAS', 'NT', 'ACT'].includes(s)
				) as AustralianState[];
			selectedStates = states;
		}

		// Parse selected location
		const selectedParam = url.searchParams.get('selected');
		if (selectedParam && locations.data?.locations) {
			const loc = locations.data.locations.find((l) => l.id === selectedParam);
			if (loc) {
				selectedLocation = loc;
			}
		}
	});

	// Sync filters to URL
	function syncToUrl() {
		if (!browser) return;

		const params = new URLSearchParams();

		// Only add type if not all types selected
		if (selectedTypes.length < 2) {
			params.set('type', selectedTypes.join(','));
		}

		// Add state filter
		if (selectedStates.length > 0) {
			params.set('state', selectedStates.join(','));
		}

		// Add selected location
		if (selectedLocation) {
			params.set('selected', selectedLocation.id);
		}

		const url = params.toString() ? `?${params.toString()}` : '/map';
		replaceState(url, {});
	}

	// Filter locations based on current filters
	const filteredLocations = $derived.by(() => {
		if (!locations.data?.locations) return [];

		let filtered = locations.data.locations.filter((loc) => {
			// Type filter - location matches if it has ANY of the selected types
			const matchesType = loc.types.some((t) => selectedTypes.includes(t));
			if (!matchesType) return false;

			// State filter - if no states selected, show all; otherwise filter
			if (selectedStates.length > 0 && !selectedStates.includes(loc.state)) {
				return false;
			}

			return true;
		});

		// Sort by distance if user location is available
		if (userLocation) {
			const userLat = userLocation.lat;
			const userLng = userLocation.lng;
			filtered = [...filtered].sort((a, b) => {
				const distA = calculateDistance(userLat, userLng, a.coordinates.lat, a.coordinates.lng);
				const distB = calculateDistance(userLat, userLng, b.coordinates.lat, b.coordinates.lng);
				return distA - distB;
			});
		}

		return filtered;
	});

	// Event handlers
	function handleTypesChange(types: LocationType[]) {
		selectedTypes = types;
		syncToUrl();
	}

	function handleStatesChange(states: AustralianState[]) {
		selectedStates = states;
		syncToUrl();
	}

	function handleSelectLocation(location: Location) {
		selectedLocation = selectedLocation?.id === location.id ? null : location;
		syncToUrl();
	}

	function handleCloseDetail() {
		selectedLocation = null;
		syncToUrl();
	}

	function handleMapReady(mapInstance: LeafletMap) {
		map = mapInstance;
	}

	// Get store name for selected location
	const selectedStoreName = $derived(
		selectedLocation?.storeId ? storeNames[selectedLocation.storeId] : undefined
	);
</script>

<svelte:head>
	<title>Map - GSAU.gg</title>
	<meta
		name="description"
		content="Find gel blaster stores and fields across Australia. Browse locations, get directions, and discover places to play."
	/>
	<link rel="canonical" href="https://www.gsau.gg/map" />
	<meta property="og:title" content="Map - GSAU.gg" />
	<meta property="og:description" content="Find gel blaster stores and fields across Australia." />
	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://www.gsau.gg/map" />
</svelte:head>

{#if locations.isLoading}
	<div class="flex h-[calc(100dvh-56px-48px)] items-center justify-center">
		<div class="flex items-center gap-2 text-muted-foreground">
			<Spinner />
			<span>Loading locations...</span>
		</div>
	</div>
{:else if locations.isError}
	<div class="p-4">
		<Alert.Root variant="destructive">
			<svg
				class="h-4 w-4"
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
				/>
			</svg>
			<Alert.Title>Error loading locations</Alert.Title>
			<Alert.Description>Please try refreshing the page.</Alert.Description>
		</Alert.Root>
	</div>
{:else}
	<!-- Shared map container - single instance for both layouts -->
	<div class="relative h-[calc(100dvh-56px-64px)] lg:h-[calc(100dvh-56px-48px)]">
		<!-- Desktop sidebar - absolutely positioned on left -->
		<div class="absolute left-0 top-0 z-[1000] hidden h-full w-80 flex-col gap-4 p-4 lg:flex">
			<!-- Filters -->
			<div class="shrink-0 rounded-lg border border-border bg-card p-4 shadow-lg">
				<MapFilters
					locations={locations.data?.locations ?? []}
					{selectedTypes}
					{selectedStates}
					onTypesChange={handleTypesChange}
					onStatesChange={handleStatesChange}
				/>
			</div>

			<!-- Location list -->
			<div
				class="min-h-0 flex-1 overflow-y-auto rounded-lg border border-border bg-card p-2 shadow-lg"
			>
				<MapSidebar
					locations={filteredLocations}
					{selectedLocation}
					{userLocation}
					onSelectLocation={handleSelectLocation}
				/>
			</div>
		</div>

		<!-- Map - full width, single instance -->
		<div class="h-full w-full">
			<LeafletMapComponent onMapReady={handleMapReady} />
			<MapMarkers
				{map}
				locations={filteredLocations}
				{selectedLocation}
				onSelectLocation={handleSelectLocation}
			/>
			<UserLocationMarker {map} {userLocation} />
		</div>

		<!-- Locate me button - positioned above mobile detail card when shown -->
		<div
			class="absolute right-4 z-[1000] {selectedLocation
				? 'bottom-44'
				: 'bottom-20'} transition-[bottom] duration-200 lg:bottom-4"
		>
			<Button
				variant={userLocation ? 'default' : 'secondary'}
				size="icon"
				class="h-10 w-10 rounded-full shadow-lg {userLocation ? 'ring-2 ring-primary/30' : ''}"
				onclick={locateUser}
				disabled={locatingUser}
				title={userLocation ? 'Update location' : 'Find my location'}
			>
				{#if locatingUser}
					<Spinner />
				{:else}
					<!-- Crosshair/target icon -->
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="20"
						height="20"
						viewBox="0 0 24 24"
						fill={userLocation ? 'currentColor' : 'none'}
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<circle cx="12" cy="12" r="10" />
						<line x1="22" y1="12" x2="18" y2="12" />
						<line x1="6" y1="12" x2="2" y2="12" />
						<line x1="12" y1="6" x2="12" y2="2" />
						<line x1="12" y1="22" x2="12" y2="18" />
					</svg>
				{/if}
			</Button>
			{#if locationError}
				<div
					class="absolute bottom-full right-0 mb-2 animate-pulse whitespace-nowrap rounded bg-destructive px-2 py-1 text-xs text-destructive-foreground shadow"
				>
					{locationError}
				</div>
			{/if}
		</div>

		<!-- Desktop: Selected location detail (top right) -->
		{#if selectedLocation}
			<div class="absolute right-4 top-4 z-[1000] hidden w-72 lg:block">
				<LocationDetail
					location={selectedLocation}
					storeName={selectedStoreName}
					onClose={handleCloseDetail}
				/>
			</div>
		{/if}

		<!-- Mobile: Selected location detail (bottom) -->
		{#if selectedLocation}
			<div class="absolute inset-x-4 bottom-20 z-[1000] lg:hidden">
				<LocationDetail
					location={selectedLocation}
					storeName={selectedStoreName}
					onClose={handleCloseDetail}
				/>
			</div>
		{/if}
	</div>

	<!-- Mobile bottom sheet -->
	<div class="lg:hidden">
		<MobileMapSheet
			locations={locations.data?.locations ?? []}
			{filteredLocations}
			{selectedTypes}
			{selectedStates}
			{selectedLocation}
			{userLocation}
			onTypesChange={handleTypesChange}
			onStatesChange={handleStatesChange}
			onSelectLocation={handleSelectLocation}
		/>
	</div>
{/if}
