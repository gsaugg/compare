import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import handlebars from 'vite-plugin-handlebars';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    tailwindcss(),
    handlebars({
      partialDirectory: resolve(__dirname, 'src/partials'),
      helpers: {
        eq: (a, b) => a === b,
      },
      context(pagePath) {
        const contexts = {
          '/index.html': { title: 'GSAU.gg - Price Comparison', activePage: 'index' },
          '/tracker.html': { title: 'Price Tracker - GSAU.gg', activePage: 'tracker' },
          '/status.html': { title: 'Scraper Status - GSAU.gg', activePage: 'status' },
          '/about.html': { title: 'About - GSAU.gg', activePage: 'about' },
        };
        return contexts[pagePath] || {};
      },
    }),
  ],
  base: './',
  root: 'src',
  publicDir: '../public',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'src/index.html'),
        status: resolve(__dirname, 'src/status.html'),
        about: resolve(__dirname, 'src/about.html'),
        tracker: resolve(__dirname, 'src/tracker.html'),
      },
    },
  },
});
