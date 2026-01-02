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
			precompress: false,
			strict: true
		}),
		paths: {
			base: ''
		},
		prerender: {
			handleHttpError: ({ path, message }) => {
				// Ignore missing favicon during prerender
				if (path === '/favicon.ico') {
					return;
				}
				throw new Error(message);
			}
		}
	}
};

export default config;
