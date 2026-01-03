<script lang="ts">
	import { browser } from '$app/environment';
	import type { Map as LeafletMap, Marker, DivIcon } from 'leaflet';

	interface Props {
		map: LeafletMap | null;
		userLocation: { lat: number; lng: number } | null;
	}

	let { map, userLocation }: Props = $props();

	let marker: Marker | null = null;
	let L: typeof import('leaflet') | null = $state(null);

	// Load Leaflet once
	$effect(() => {
		if (browser && !L) {
			import('leaflet').then((leaflet) => {
				L = leaflet.default;
			});
		}
	});

	// Create pulsing user location marker
	function createUserIcon(): DivIcon | null {
		if (!L) return null;

		return L.divIcon({
			className: 'user-location-marker',
			html: `
				<div class="user-marker-outer"></div>
				<div class="user-marker-inner"></div>
			`,
			iconSize: [24, 24],
			iconAnchor: [12, 12]
		});
	}

	// Manage marker lifecycle
	$effect(() => {
		if (!map || !L) return;

		if (!userLocation) {
			// Remove marker if no location
			if (marker) {
				marker.remove();
				marker = null;
			}
			return;
		}

		const icon = createUserIcon();
		if (!icon) return;

		if (marker) {
			// Update existing marker position
			marker.setLatLng([userLocation.lat, userLocation.lng]);
		} else {
			// Create new marker
			marker = L.marker([userLocation.lat, userLocation.lng], {
				icon,
				zIndexOffset: 1000 // Above other markers
			}).addTo(map);
		}

		// Cleanup on unmount
		return () => {
			if (marker) {
				marker.remove();
				marker = null;
			}
		};
	});
</script>

<style>
	:global(.user-location-marker) {
		position: relative;
	}

	:global(.user-marker-outer) {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 24px;
		height: 24px;
		margin-left: -12px;
		margin-top: -12px;
		background: rgba(59, 130, 246, 0.3);
		border-radius: 50%;
		animation: pulse 2s ease-out infinite;
	}

	:global(.user-marker-inner) {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 12px;
		height: 12px;
		margin-left: -6px;
		margin-top: -6px;
		background: #3b82f6;
		border: 2px solid white;
		border-radius: 50%;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
	}

	@keyframes pulse {
		0% {
			transform: scale(1);
			opacity: 1;
		}
		100% {
			transform: scale(2);
			opacity: 0;
		}
	}
</style>
