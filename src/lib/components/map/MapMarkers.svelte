<script lang="ts">
	import { browser } from '$app/environment';
	import type { Map as LeafletMap, Marker, LayerGroup } from 'leaflet';
	import type { Location } from '$lib/data/types';
	import { createLocationMarker } from './markers';

	interface Props {
		map: LeafletMap | null;
		locations: Location[];
		selectedLocation: Location | null;
		onSelectLocation: (location: Location) => void;
		userLocation?: { lat: number; lng: number } | null;
	}

	let { map, locations, selectedLocation, onSelectLocation, userLocation = null }: Props = $props();

	let L: typeof import('leaflet') | null = $state(null);
	let markerLayer: LayerGroup | null = null;
	let markersMap = new Map<string, Marker>();
	let initialFitDone = false;
	let prevLocationIds = '';

	// Load Leaflet dynamically
	$effect(() => {
		if (browser && !L) {
			import('leaflet').then((leaflet) => {
				L = leaflet.default;
			});
		}
	});

	// Manage markers when map or locations change (NOT selection)
	$effect(() => {
		if (!map || !L) return;

		// Create a stable ID string to detect actual location list changes
		const currentLocationIds = locations.map((l) => l.id).join(',');
		const locationsChanged = currentLocationIds !== prevLocationIds;

		// Only recreate markers if locations actually changed
		if (!locationsChanged && markerLayer) return;

		prevLocationIds = currentLocationIds;

		// Create marker layer if it doesn't exist
		if (!markerLayer) {
			markerLayer = L.layerGroup().addTo(map);
		}

		// Clear existing markers
		markerLayer.clearLayers();
		markersMap.clear();

		// Add markers for each location (without selection state - that's handled by next effect)
		for (const location of locations) {
			const icon = createLocationMarker(L, location.types, false);

			const marker = L.marker([location.coordinates.lat, location.coordinates.lng], {
				icon,
				title: location.name,
				alt: location.name,
				riseOnHover: true
			});

			marker.on('click', () => {
				onSelectLocation(location);
			});

			marker.addTo(markerLayer);
			markersMap.set(location.id, marker);
		}

		// Fit bounds to show all markers on initial load (skip if user location is available)
		if (!initialFitDone && locations.length > 0 && !userLocation) {
			const bounds = L.latLngBounds(
				locations.map((loc) => [loc.coordinates.lat, loc.coordinates.lng])
			);
			// Sidebar is w-80 (320px) + p-4 (16px) = 336px, add buffer
			const isDesktop = window.innerWidth >= 1024;
			map.fitBounds(bounds, {
				paddingTopLeft: isDesktop ? [340, 20] : [20, 20],
				paddingBottomRight: isDesktop ? [20, 20] : [20, 120]
			});
			initialFitDone = true;
		}

		// Cleanup on unmount
		return () => {
			if (markerLayer) {
				markerLayer.remove();
				markerLayer = null;
			}
			markersMap.clear();
		};
	});

	// Handle selection changes separately (just update icons, don't recreate markers)
	$effect(() => {
		if (!L || !map || markersMap.size === 0) return;

		// Update icons for selection state
		for (const location of locations) {
			const marker = markersMap.get(location.id);
			if (marker) {
				const isSelected = selectedLocation?.id === location.id;
				marker.setIcon(createLocationMarker(L, location.types, isSelected));
			}
		}

		// Fly to selected location
		if (selectedLocation) {
			map.flyTo(
				[selectedLocation.coordinates.lat, selectedLocation.coordinates.lng],
				Math.max(map.getZoom(), 10),
				{ duration: 0.5 }
			);
		}
	});
</script>
