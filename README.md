# GSAU.gg

Price comparison tool for Australian gel blaster products. Aggregates pricing from 17 retailers and updates hourly.

**Live site:** https://www.gsau.gg

## Features

- Search and filter across 20,000+ products from 17 stores
- Compare prices from multiple stores side-by-side
- **1-year price history** with interactive charts per vendor
- **Price change badges** (↓/↑ %) for changes within the last 7 days
- Filter by category, multiple stores, stock status, and price range
- Sort by price, discount percentage, or name
- Infinite scroll with auto-loading
- Multi-select store filter with checkboxes
- Responsive mobile sidebar with slide-out drawer
- Light/dark mode with system preference detection
- Keyboard shortcuts (`/` to search, `Esc` to close sidebar)
- [Scraper status dashboard](https://www.gsau.gg/status) with per-store logs
- [Price tracker](https://www.gsau.gg/tracker) showing recent price drops/increases and new products

## Tech Stack

- **Frontend:** SvelteKit 2, Svelte 5, Tailwind CSS v4, shadcn-svelte
- **Data fetching:** TanStack Query (svelte-query)
- **Charts:** Chart.js (lazy loaded)
- **Search:** Fuse.js
- **Validation:** Zod
- **Analytics:** Google Analytics 4 (with store click tracking)
- **Scraper:** Python (requests, rapidfuzz, pyahocorasick)
- **Build:** Vite
- **Hosting:** GitHub Pages (static adapter)

## Development

```bash
# Install dependencies
npm install
uv sync

# Run dev server
npm run dev

# Build for production
npm run build

# Type check
npm run check

# Run scraper
uv run python scripts/scrape.py

# Run scraper with cached data (for testing)
uv run python scripts/scrape.py --offline

# Format code
npm run format
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
