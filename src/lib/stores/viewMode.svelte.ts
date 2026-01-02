import { browser } from '$app/environment';

export type ViewMode = 'grid' | 'list';

const STORAGE_KEY = 'gsau-view-mode';

/**
 * Safely get item from localStorage
 * Returns null if unavailable (private browsing, quota exceeded, etc.)
 */
function getStoredViewMode(): ViewMode | null {
	if (!browser) return null;
	try {
		const stored = localStorage.getItem(STORAGE_KEY);
		if (stored === 'list' || stored === 'grid') {
			return stored;
		}
		return null;
	} catch {
		// localStorage may be unavailable (private browsing, quota exceeded)
		return null;
	}
}

/**
 * Safely set item in localStorage
 * Silently fails if unavailable
 */
function saveViewMode(mode: ViewMode): void {
	if (!browser) return;
	try {
		localStorage.setItem(STORAGE_KEY, mode);
	} catch {
		// Ignore localStorage errors
	}
}

function createViewModeStore() {
	// Initialize from localStorage or default to 'grid'
	let mode = $state<ViewMode>(getStoredViewMode() ?? 'grid');

	return {
		get value() {
			return mode;
		},
		set(newMode: ViewMode) {
			mode = newMode;
			saveViewMode(newMode);
		},
		toggle() {
			const newMode = mode === 'grid' ? 'list' : 'grid';
			mode = newMode;
			saveViewMode(newMode);
		}
	};
}

export const viewMode = createViewModeStore();
