# GSAU.gg

Price comparison tool for Australian gel blaster products. Aggregates pricing from 14+ retailers and updates every 30 minutes.

**Live site:** https://www.gsau.gg

## Features

- Search and filter across 11,500+ products from 15 stores
- Compare prices from multiple stores side-by-side
- Filter by category, multiple stores, stock status, and price range
- Sort by price, discount percentage, or name
- Infinite scroll with auto-loading
- Multi-select store filter with checkboxes
- Responsive mobile sidebar with slide-out drawer
- 32 themes with auto-detect light/dark mode
- Keyboard shortcuts (`/` to search, `Esc` to close sidebar)
- [Scraper status dashboard](https://www.gsau.gg/status.html) with per-store logs

## Tech Stack

- **Frontend:** Alpine.js, Tailwind CSS, DaisyUI, Fuse.js
- **Scraper:** Python (requests, rapidfuzz, pyahocorasick)
- **Build:** Vite
- **Hosting:** GitHub Pages

## Development

```bash
# Install dependencies
npm install
uv sync

# Run dev server
npm run dev

# Run scraper
uv run python scripts/scrape.py

# Run scraper with cached data (for testing)
uv run python scripts/scrape.py --offline

# Lint
npm run lint
uv run ruff check scripts/
```

## Adding a Store

1. Add entry to `stores.json`:
   ```json
   {
     "name": "Store Name",
     "url": "https://store.com",
     "platform": "shopify|woocommerce|squarespace",
     "enabled": true
   }
   ```
2. Run scraper to test
3. Add exclusion keywords to `scripts/filters.py` if needed

## License

AGPL-3.0 - See [LICENSE](LICENSE)
