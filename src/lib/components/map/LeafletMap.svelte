<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { theme, type Theme } from '$lib/stores/theme.svelte';
	import type { Map as LeafletMap, TileLayer } from 'leaflet';

	interface Props {
		onMapReady?: (map: LeafletMap) => void;
		class?: string;
	}

	let { onMapReady, class: className = '' }: Props = $props();

	let mapContainer: HTMLDivElement | null = $state(null);
	let map: LeafletMap | null = $state(null);
	let tileLayer: TileLayer | null = $state(null);

	// Tile URLs
	const LIGHT_TILES = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
	const DARK_TILES = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
	const ATTRIBUTION =
		'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

	// Australia center coordinates
	const AUSTRALIA_CENTER: [number, number] = [-25.27, 133.78];
	const DEFAULT_ZOOM = 4;

	// Resolve theme to actual dark/light value
	function getResolvedTheme(t: Theme): 'light' | 'dark' {
		if (t === 'system') {
			return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		}
		return t;
	}

	// Watch for theme changes and update tiles
	const currentTheme = $derived(theme.value);

	$effect(() => {
		if (!browser || !map || !tileLayer) return;

		const resolved = getResolvedTheme(currentTheme);
		const newUrl = resolved === 'dark' ? DARK_TILES : LIGHT_TILES;
		tileLayer.setUrl(newUrl);
	});

	onMount(() => {
		if (!mapContainer) return;

		let mapInstance: LeafletMap | null = null;

		// Dynamic import for SSR compatibility
		(async () => {
			const L = await import('leaflet');
			await import('leaflet/dist/leaflet.css');

			if (!mapContainer) return;

			// Create map
			mapInstance = L.map(mapContainer, {
				center: AUSTRALIA_CENTER,
				zoom: DEFAULT_ZOOM,
				zoomControl: true,
				attributionControl: true
			});

			// Determine initial tile URL based on theme
			const resolved = getResolvedTheme(theme.value);
			const initialUrl = resolved === 'dark' ? DARK_TILES : LIGHT_TILES;

			// Add tile layer
			const tiles = L.tileLayer(initialUrl, {
				attribution: ATTRIBUTION,
				maxZoom: 18,
				subdomains: 'abcd'
			}).addTo(mapInstance);

			map = mapInstance;
			tileLayer = tiles;

			// Notify parent that map is ready
			onMapReady?.(mapInstance);
		})();

		// Cleanup on unmount
		return () => {
			if (mapInstance) {
				mapInstance.remove();
			}
		};
	});
</script>

<div bind:this={mapContainer} class="h-full w-full {className}" role="application" aria-label="Map">
	{#if !browser}
		<div class="flex h-full items-center justify-center bg-muted">
			<span class="text-muted-foreground">Loading map...</span>
		</div>
	{/if}
</div>
