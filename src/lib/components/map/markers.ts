import type { DivIcon } from 'leaflet';
import type { LocationType } from '$lib/data/types';

// Marker colors matching site theme
const STORE_COLOR = '#14b8a6'; // teal (primary)
const FIELD_COLOR = '#22c55e'; // green (stock-available)

/**
 * Creates a custom DivIcon marker for a location
 * @param types - Array of location types (['store'], ['field'], or ['store', 'field'])
 * @param selected - Whether the marker is currently selected
 */
export function createLocationMarker(
	L: typeof import('leaflet'),
	types: LocationType[],
	selected = false
): DivIcon {
	const isStore = types.includes('store');
	const isField = types.includes('field');
	const isCombo = isStore && isField;

	// Determine marker style based on type
	let bgColor: string;
	let borderColor: string;
	let ringColor: string | null = null;

	if (isCombo) {
		// Combo: teal with green ring
		bgColor = STORE_COLOR;
		borderColor = STORE_COLOR;
		ringColor = FIELD_COLOR;
	} else if (isField) {
		// Field only: green
		bgColor = FIELD_COLOR;
		borderColor = FIELD_COLOR;
	} else {
		// Store only (default): teal
		bgColor = STORE_COLOR;
		borderColor = STORE_COLOR;
	}

	// Size adjustments for selected state (larger for better visibility at low zoom)
	const size = selected ? 36 : 28;
	const innerSize = selected ? 24 : 18;

	// Build the marker HTML
	let html = `
		<div class="location-marker ${selected ? 'selected' : ''}" style="
			width: ${size}px;
			height: ${size}px;
			position: relative;
			display: flex;
			align-items: center;
			justify-content: center;
		">
	`;

	// Add outer ring for combo markers
	if (ringColor) {
		html += `
			<div style="
				position: absolute;
				width: ${size}px;
				height: ${size}px;
				border-radius: 50%;
				border: 3px solid ${ringColor};
				box-sizing: border-box;
			"></div>
		`;
	}

	// Add main marker circle
	html += `
		<div style="
			width: ${innerSize}px;
			height: ${innerSize}px;
			background-color: ${bgColor};
			border: 2px solid white;
			border-radius: 50%;
			box-shadow: 0 2px 4px rgba(0,0,0,0.3);
			${selected ? 'transform: scale(1.1);' : ''}
		"></div>
	</div>
	`;

	return L.divIcon({
		html,
		className: 'custom-location-marker',
		iconSize: [size, size],
		iconAnchor: [size / 2, size / 2],
		popupAnchor: [0, -size / 2]
	});
}

/**
 * Get the primary color for a location type (for legend/UI)
 */
export function getLocationTypeColor(types: LocationType[]): string {
	const isStore = types.includes('store');
	const isField = types.includes('field');

	if (isStore && isField) {
		return STORE_COLOR; // Combo uses store color as primary
	} else if (isField) {
		return FIELD_COLOR;
	}
	return STORE_COLOR;
}

/**
 * Get label for location type(s)
 */
export function getLocationTypeLabel(types: LocationType[]): string {
	const isStore = types.includes('store');
	const isField = types.includes('field');

	if (isStore && isField) {
		return 'Store & Field';
	} else if (isField) {
		return 'Field';
	}
	return 'Store';
}
