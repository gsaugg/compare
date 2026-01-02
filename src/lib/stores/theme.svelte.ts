// Theme store with system preference detection and localStorage persistence
// Migrated to Svelte 5 runes pattern
import { browser } from '$app/environment';

export type Theme = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'gsau_theme';

function getSystemTheme(): 'light' | 'dark' {
	if (!browser) return 'light';
	return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function getStoredTheme(): Theme | null {
	if (!browser) return null;
	try {
		const stored = localStorage.getItem(STORAGE_KEY);
		if (stored === 'light' || stored === 'dark' || stored === 'system') {
			return stored;
		}
		return null;
	} catch {
		// localStorage may be unavailable (private browsing, quota exceeded)
		return null;
	}
}

function saveTheme(theme: Theme): void {
	if (!browser) return;
	try {
		localStorage.setItem(STORAGE_KEY, theme);
	} catch {
		// Ignore localStorage errors
	}
}

function applyTheme(theme: Theme): void {
	if (!browser) return;

	const resolved = theme === 'system' ? getSystemTheme() : theme;
	const root = document.documentElement;

	// Remove both classes first
	root.classList.remove('light', 'dark');

	// Apply the resolved theme class
	root.classList.add(resolved);
}

function createThemeStore() {
	// Initialize from localStorage or default to 'system'
	let currentTheme = $state<Theme>(getStoredTheme() ?? 'system');

	// Apply initial theme
	if (browser) {
		applyTheme(currentTheme);

		// Listen for system preference changes
		// Use a named function so we can properly reference it
		const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
		const handleSystemChange = () => {
			// Only react if user prefers system theme
			if (currentTheme === 'system') {
				applyTheme('system');
			}
		};

		// Modern browsers support addEventListener
		mediaQuery.addEventListener('change', handleSystemChange);

		// Note: For module-level stores, cleanup isn't typically needed
		// as the store lives for the app's lifetime. However, for HMR
		// during development, this could cause multiple listeners.
		// In production, this is not an issue.
	}

	return {
		get value() {
			return currentTheme;
		},
		set(theme: Theme) {
			currentTheme = theme;
			saveTheme(theme);
			applyTheme(theme);
		},
		toggle() {
			const resolved = currentTheme === 'system' ? getSystemTheme() : currentTheme;
			const next: Theme = resolved === 'light' ? 'dark' : 'light';
			currentTheme = next;
			saveTheme(next);
			applyTheme(next);
		}
	};
}

export const theme = createThemeStore();
