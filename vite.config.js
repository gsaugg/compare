import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'path';

export default defineConfig({
  plugins: [tailwindcss()],
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
