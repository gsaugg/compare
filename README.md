# GSAU.gg

Price comparison tool for Australian gel blaster products. Aggregates pricing from 14+ retailers and updates hourly.

**Live site:** https://www.gsau.gg

## Features

- Search and filter across 13,000+ products from 16 stores
- Compare prices from multiple stores side-by-side
- **30-day price history** with interactive charts per vendor
- **Price change badges** (↓/↑ %) for changes within the last 7 days
- Filter by category, multiple stores, stock status, and price range
- Sort by price, discount percentage, or name
- Infinite scroll with auto-loading
- Multi-select store filter with checkboxes
- Responsive mobile sidebar with slide-out drawer
- 32 themes with auto-detect light/dark mode
- Keyboard shortcuts (`/` to search, `Esc` to close sidebar)
- [Scraper status dashboard](https://www.gsau.gg/status.html) with per-store logs
- [Price tracker](https://www.gsau.gg/tracker.html) showing recent price drops/increases and new products

## Tech Stack

- **Frontend:** Alpine.js, Tailwind CSS, DaisyUI, Fuse.js, Chart.js
- **Analytics:** Google Analytics 4 (with store click tracking)
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
     "id": "st",
     "name": "Store Name",
     "url": "https://store.com",
     "platform": "shopify|woocommerce|squarespace",
     "enabled": true
   }
   ```
2. Run scraper to test
3. Add exclusion keywords to `scripts/filters.py` if needed

## Contact

- **Email:** hello@gsau.gg
- **Discord:** [Gelsoft AU](https://discord.gg/rmfZtWD95f)
- **Issues:** [GitHub Issues](https://github.com/gsaugg/compare/issues)

## License

AGPL-3.0 - See [LICENSE](LICENSE)
