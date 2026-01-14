// Enable prerendering for all pages (static site)
export const prerender = true;

// Enable SSR so <svelte:head> renders meta tags during prerendering
export const ssr = true;

// Use trailing slashes for consistent URLs - prevents duplicate content issues
// where both /page and /page/ serve the same content on GitHub Pages
export const trailingSlash = 'always';
