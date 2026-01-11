import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),

	kit: {
		adapter: adapter({
			pages: 'dist',
			assets: 'dist',
			fallback: undefined,
			precompress: true,
			strict: true
		}),
		paths: {
			base: ''
		},
		prerender: {
			handleHttpError: ({ path, message }) => {
				// Ignore missing favicon/icon files during prerender (user will add later)
				if (
					path === '/favicon.ico' ||
					path.startsWith('/favicon-') ||
					path === '/apple-touch-icon.png' ||
					path === '/og-default.png'
				) {
					return;
				}
				throw new Error(message);
			}
		}
	}
};

export default config;
