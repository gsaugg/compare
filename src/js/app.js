import Alpine from 'alpinejs';
import Fuse from 'fuse.js';
import { Chart, registerables } from 'chart.js';
import 'chartjs-adapter-date-fns';

// Register Chart.js components
Chart.register(...registerables);

// ========== CONSTANTS ==========
const TOAST_DURATION_MS = 5000;
const STALE_DATA_THRESHOLD_MS = 3 * 60 * 60 * 1000; // 3 hours - scraper runs hourly
const FUSE_THRESHOLD = 0.3;

// ========== SEARCH HELPERS ==========
/**
 * Normalize text for search matching.
 * Converts hyphens/dashes to spaces so "KS-1", "KS 1", and "KS1" all match.
 * Returns both spaced and compact versions for comprehensive matching.
 */
function normalizeForSearch(text, includeCompact = true) {
  if (!text) return '';
  const withSpaces = text
    .replace(/[-–—]/g, ' ') // Replace hyphens/dashes with spaces
    .replace(/\s+/g, ' ') // Collapse multiple spaces
    .toLowerCase()
    .trim();
  if (!includeCompact) return withSpaces;
  // Include compact version (no spaces) to match "KS1" against "KS-1"
  const compact = withSpaces.replace(/\s+/g, '');
  return `${withSpaces} ${compact}`;
}
const DEFAULT_PER_PAGE = 60;
const FETCH_TIMEOUT_MS = 10000;
const MAX_SEARCH_CACHE_SIZE = 10;
const PRICE_CHANGE_DAYS = 7; // Show price changes from last 7 days

// ========== THEME STORE (shared across components) ==========
Alpine.store('theme', {
  current: 'light',
  themes: [
    'light',
    'dark',
    'cupcake',
    'bumblebee',
    'emerald',
    'corporate',
    'synthwave',
    'retro',
    'cyberpunk',
    'valentine',
    'halloween',
    'garden',
    'forest',
    'aqua',
    'lofi',
    'pastel',
    'fantasy',
    'wireframe',
    'black',
    'luxury',
    'dracula',
    'cmyk',
    'autumn',
    'business',
    'acid',
    'lemonade',
    'night',
    'coffee',
    'winter',
    'dim',
    'nord',
    'sunset',
  ],

  init() {
    const saved = localStorage.getItem('theme');
    if (this.themes.includes(saved)) {
      this.current = saved;
    } else {
      // Auto-detect system preference
      this.current = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    this.apply();
  },

  set(theme) {
    if (this.themes.includes(theme)) {
      this.current = theme;
      this.apply();
    }
  },

  apply() {
    document.documentElement.setAttribute('data-theme', this.current);
    localStorage.setItem('theme', this.current);
  },
});

// ========== PRODUCT APP COMPONENT ==========
Alpine.data('productApp', () => ({
  // ===== STATE =====
  allProducts: [],
  filteredProducts: [],
  categories: [],
  vendors: [],
  fuse: null,
  search: '',
  category: '',
  selectedVendors: [],
  stock: 'instock',
  sort: 'discount-pct',
  perPage: String(DEFAULT_PER_PAGE),
  minPrice: null,
  maxPrice: null,
  displayedCount: 0,
  previousSort: 'discount-pct',
  _lastSearchWasActive: false,
  lastUpdated: '',
  loading: true,
  error: null,
  sidebarOpen: false,
  toast: null,
  showVendors: 'best',
  searchTags: false,
  expandedProducts: {},
  _searchCache: new Map(),
  showScrollTop: false,
  viewMode: 'card',
  trackerData: {},
  chartModal: null, // { product, chart } when open
  _chartInstance: null,

  // ===== COMPUTED =====
  get theme() {
    return this.$store.theme.current;
  },

  get displayedProducts() {
    if (this.perPage === 'all') {
      return this.filteredProducts;
    }
    return this.filteredProducts.slice(0, this.displayedCount);
  },

  get hasMore() {
    return this.displayedCount < this.filteredProducts.length;
  },

  get remainingCount() {
    return this.filteredProducts.length - this.displayedCount;
  },

  // ===== LIFECYCLE =====
  async init() {
    // Initialize theme store
    this.$store.theme.init();

    // Load filters from URL
    this.loadFiltersFromURL();

    // Watch for filter changes (search uses x-model.debounce in HTML)
    this.$watch('search', () => this.applyFilters());
    this.$watch('category', () => this.applyFilters());
    this.$watch('selectedVendors', () => this.applyFilters());
    this.$watch('stock', () => this.applyFilters());
    this.$watch('sort', () => this.applyFilters());
    this.$watch('perPage', () => this.resetDisplay());
    this.$watch('searchTags', () => this.rebuildFuseIndex());
    this.$watch('minPrice', () => this.applyFilters());
    this.$watch('maxPrice', () => this.applyFilters());
    this.$watch('viewMode', () => this.updateURL());

    // Setup keyboard shortcuts
    this.setupKeyboardShortcuts();

    // Load products and price history in parallel
    await Promise.all([this.loadProducts(), this.loadPriceHistory()]);

    // Setup infinite scroll
    this.setupInfiniteScroll();

    // Setup scroll-to-top button
    this.setupScrollTopButton();
  },

  // ===== KEYBOARD SHORTCUTS =====
  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // "/" to focus search (when not in input)
      if (
        e.key === '/' &&
        !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)
      ) {
        e.preventDefault();
        document.getElementById('search')?.focus();
      }
      // Escape to close sidebar
      if (e.key === 'Escape') {
        this.sidebarOpen = false;
      }
    });
  },

  // ===== INFINITE SCROLL =====
  setupInfiniteScroll() {
    const sentinel = document.getElementById('scroll-sentinel');
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && this.hasMore && !this.loading) {
          this.loadMore();
        }
      },
      { rootMargin: '200px' }
    );

    observer.observe(sentinel);
  },

  // ===== SCROLL TO TOP =====
  setupScrollTopButton() {
    window.addEventListener(
      'scroll',
      () => {
        this.showScrollTop = window.scrollY > 400;
      },
      { passive: true }
    );
  },

  scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  },

  // ===== DATA LOADING =====
  async loadProducts(retryCount = 0) {
    try {
      this.loading = true;
      this.error = null;

      const response = await this.fetchWithTimeout('./data/products.json', FETCH_TIMEOUT_MS);
      if (!response.ok) throw new Error(`HTTP ${response.status}: Failed to load products`);

      const data = await response.json();

      // Validate data structure
      if (!Array.isArray(data.products)) {
        throw new Error('Invalid data format: products array missing');
      }

      // Process products with pre-computed values
      this.allProducts = data.products.map((p) => {
        const vendorNames = p.vendors?.map((v) => v.name).join(' ') ?? '';
        return {
          ...p,
          _vendorNames: vendorNames,
          _searchText: normalizeForSearch(
            [p.title, p.category, vendorNames].filter(Boolean).join(' ')
          ),
          _discountPercent: this.calculateBestDiscount(p, 'percent'),
          _discountDollars: this.calculateBestDiscount(p, 'dollars'),
        };
      });

      // Cache categories and vendors (computed once)
      this.categories = [...new Set(this.allProducts.map((p) => p.category))]
        .filter(Boolean)
        .sort();

      const vendorSet = new Set();
      this.allProducts.forEach((p) => {
        p.vendors?.forEach((v) => vendorSet.add(v.name));
      });
      this.vendors = [...vendorSet].sort((a, b) =>
        a.localeCompare(b, undefined, { sensitivity: 'base' })
      );

      // Initialize Fuse.js for search
      this.rebuildFuseIndex();

      // Update last updated time
      this.lastUpdated = data.lastUpdated ? new Date(data.lastUpdated).toLocaleString() : '';

      // Check for stale data (>1 hour old = 2+ missed scraper runs)
      if (data.lastUpdated) {
        const dataAge = Date.now() - new Date(data.lastUpdated).getTime();
        if (dataAge > STALE_DATA_THRESHOLD_MS) {
          const hoursOld = Math.round(dataAge / (60 * 60 * 1000));
          this.showToast(`Data is ${hoursOld}+ hours old. Prices may be outdated.`, 'warning', {
            text: 'Refresh',
            handler: () => {
              // Force bypass browser cache
              window.location.href = window.location.pathname + '?_=' + Date.now();
            },
          });
        }
      }

      this.applyFilters();
    } catch (err) {
      console.error('Error loading products:', err);
      this.error = err?.message ?? 'An unknown error occurred';

      // Auto-retry on failure (max 2 retries)
      if (retryCount < 2) {
        this.showToast(`${this.error} - Retrying...`, 'warning');
        setTimeout(() => this.loadProducts(retryCount + 1), 2000);
      } else {
        this.showToast('Failed to load products after multiple attempts', 'error');
      }
    } finally {
      this.loading = false;
    }
  },

  async fetchWithTimeout(url, timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, { signal: controller.signal, cache: 'no-cache' });
      clearTimeout(timeoutId);
      return response;
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new Error('Request timed out');
      }
      throw err;
    }
  },

  // ===== PRICE HISTORY =====
  async loadPriceHistory() {
    try {
      const response = await this.fetchWithTimeout('./data/tracker-data.json', FETCH_TIMEOUT_MS);
      if (!response.ok) {
        console.warn('Price history not available');
        return;
      }
      const data = await response.json();
      this.trackerData = data.history || {};
    } catch (err) {
      // Price history is optional, don't show error to user
      console.warn('Could not load price history:', err.message);
    }
  },

  getPriceChange(product) {
    // Returns { percent, direction, previousPrice } or null if no recent change
    const history = this.trackerData[product.id];
    if (!history?.lowest?.length) return null;

    const cutoff = Math.floor(Date.now() / 1000) - PRICE_CHANGE_DAYS * 24 * 60 * 60;
    const entries = history.lowest;

    // Find the most recent entry with a previous price
    for (let i = entries.length - 1; i >= 0; i--) {
      const entry = entries[i];
      if (entry.t >= cutoff && entry.prev !== undefined) {
        const percent = ((entry.prev - entry.p) / entry.prev) * 100;
        return {
          percent: Math.abs(percent),
          direction: percent > 0 ? 'down' : 'up',
          previousPrice: entry.prev,
          currentPrice: entry.p,
        };
      }
    }
    return null;
  },

  openPriceChart(product) {
    this.chartModal = { product };
    // Chart will be rendered by Alpine x-init on the canvas
  },

  closePriceChart() {
    if (this._chartInstance) {
      this._chartInstance.destroy();
      this._chartInstance = null;
    }
    this.chartModal = null;
  },

  renderPriceChart(canvas) {
    if (!this.chartModal || !canvas) return;

    const product = this.chartModal.product;
    const history = this.trackerData[product.id];
    if (!history) return;

    // Prepare datasets for each vendor
    const datasets = [];
    const colors = [
      '#3b82f6', // blue
      '#10b981', // green
      '#f59e0b', // amber
      '#ef4444', // red
      '#8b5cf6', // purple
      '#ec4899', // pink
    ];

    let colorIndex = 0;

    // Add vendor lines (sale price + regular price)
    if (history.vendors) {
      for (const [vendor, entries] of Object.entries(history.vendors)) {
        if (entries.length === 0) continue;
        const color = colors[colorIndex % colors.length];
        colorIndex++;

        // Sale price line
        const data = entries.map((e) => ({ x: e.t * 1000, y: e.p }));
        if (data.length > 0) {
          data.push({ x: Date.now(), y: data[data.length - 1].y });
        }
        datasets.push({
          label: vendor,
          data,
          borderColor: color,
          backgroundColor: color + '20',
          stepped: 'after',
          pointRadius: data.map((_, i) => (i === data.length - 1 ? 6 : 3)),
        });

        // Regular price line - only if any entry has rp different from p
        const hasRegularPrice = entries.some((e) => e.rp && e.rp !== e.p);
        if (hasRegularPrice) {
          const regularPriceData = entries.map((e) => ({ x: e.t * 1000, y: e.rp || e.p }));
          if (regularPriceData.length > 0) {
            regularPriceData.push({ x: Date.now(), y: regularPriceData[regularPriceData.length - 1].y });
          }
          datasets.push({
            label: `${vendor} (Non-discount)`,
            data: regularPriceData,
            borderColor: color + '80',
            backgroundColor: 'transparent',
            borderDash: [5, 5],
            stepped: 'after',
            pointRadius: 0,
          });
        }
      }
    }

    // Add lowest price line if we have it
    if (history.lowest?.length > 0) {
      const lowestData = history.lowest.map((e) => ({ x: e.t * 1000, y: e.p }));
      // Extend line to "now" with last known price
      if (lowestData.length > 0) {
        lowestData.push({ x: Date.now(), y: lowestData[lowestData.length - 1].y });
      }
      datasets.unshift({
        label: 'Lowest Price',
        data: lowestData,
        borderColor: '#22c55e',
        backgroundColor: '#22c55e20',
        borderWidth: 3,
        stepped: 'after',
        pointRadius: lowestData.map((_, i) => (i === lowestData.length - 1 ? 8 : 4)),
      });
    }

    // Current time for "now" line
    const now = Date.now();

    if (datasets.length === 0) return;

    // Calculate axis bounds from actual data
    const allPoints = datasets.flatMap((ds) => ds.data);
    const timestamps = allPoints.map((p) => p.x);
    const prices = allPoints.map((p) => p.y);

    const minTime = Math.min(...timestamps);
    const maxTime = Math.max(...timestamps);
    const timePadding = (maxTime - minTime) * 0.05 || 24 * 60 * 60 * 1000; // 5% or 1 day min

    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const pricePadding = (maxPrice - minPrice) * 0.1 || 1; // 10% or $1 min

    // Plugin for "Now" line and price labels
    const nowLinePlugin = {
      id: 'nowLine',
      afterDraw: (chart) => {
        const { ctx, scales } = chart;
        const xScale = scales.x;
        const yScale = scales.y;
        const nowX = xScale.getPixelForValue(now);

        // Draw vertical "Now" line
        ctx.save();
        ctx.beginPath();
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = '#888';
        ctx.lineWidth = 1;
        ctx.moveTo(nowX, yScale.top);
        ctx.lineTo(nowX, yScale.bottom);
        ctx.stroke();

        // "Now" label at top
        ctx.fillStyle = '#888';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Now', nowX, yScale.top - 5);

        // Price labels at endpoints
        chart.data.datasets.forEach((dataset) => {
          if (dataset.data.length === 0 || dataset.label.includes('Non-discount')) return;
          const lastPoint = dataset.data[dataset.data.length - 1];
          const x = xScale.getPixelForValue(lastPoint.x);
          const y = yScale.getPixelForValue(lastPoint.y);

          ctx.fillStyle = dataset.borderColor;
          ctx.font = 'bold 11px sans-serif';
          ctx.textAlign = 'left';
          ctx.fillText(`$${lastPoint.y.toFixed(2)}`, x + 10, y + 4);
        });

        ctx.restore();
      },
    };

    this._chartInstance = new Chart(canvas, {
      type: 'line',
      data: { datasets },
      plugins: [nowLinePlugin],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index',
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day',
              displayFormats: { day: 'MMM d' },
              tooltipFormat: 'MMM d, yyyy h:mm a',
            },
            min: minTime - timePadding,
            max: maxTime + timePadding,
            ticks: {
              maxTicksLimit: 10,
            },
            title: { display: true, text: 'Date' },
          },
          y: {
            min: Math.max(0, minPrice - pricePadding),
            max: maxPrice + pricePadding,
            title: { display: true, text: 'Price ($)' },
            ticks: {
              callback: (value) => '$' + value.toFixed(2),
            },
          },
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: $${ctx.parsed.y.toFixed(2)}`,
            },
          },
          legend: {
            position: 'bottom',
          },
        },
      },
    });
  },

  // ===== SEARCH INDEX =====
  rebuildFuseIndex() {
    const keys = [
      { name: '_searchText', weight: 1.0 }, // Normalized field for hyphen/space matching
      { name: 'title', weight: 0.5 }, // Keep original for exact matches
    ];

    // Only include tags if searchTags is enabled
    if (this.searchTags) {
      keys.push({ name: 'tags', weight: 0.3 });
    }

    this.fuse = new Fuse(this.allProducts, {
      keys,
      threshold: FUSE_THRESHOLD,
      ignoreLocation: true,
      includeScore: true,
      minMatchCharLength: 2,
    });

    // Clear search cache when index changes
    this._searchCache.clear();

    // Re-apply filters if we have a search term
    if (this.search.trim()) {
      this.applyFilters();
    }
  },

  // ===== FILTERING & SORTING =====
  applyFilters() {
    const rawSearch = this.search.trim();
    const searchTerm = normalizeForSearch(rawSearch, false); // Don't include compact for query
    let sortBy = this.sort;
    let baseProducts;

    if (searchTerm && this.fuse) {
      // Check search cache first
      if (this._searchCache.has(searchTerm)) {
        baseProducts = this._searchCache.get(searchTerm);
      } else {
        // Find word-based matches first (all search words must appear in title)
        const searchWords = searchTerm.toLowerCase().split(/\s+/).filter((w) => w.length >= 2);
        const exactMatches =
          searchWords.length > 0
            ? this.allProducts.filter((p) => {
                if (!p._searchText) return false;
                const textLower = p._searchText.toLowerCase();
                return searchWords.every((word) => textLower.includes(word));
              })
            : [];
        const exactIds = new Set(exactMatches.map((p) => p.id));

        // Then get fuzzy matches (excluding exact matches to avoid duplicates)
        const fuzzyResults = this.fuse.search(searchTerm);
        const fuzzyMatches = fuzzyResults.map((r) => r.item).filter((p) => !exactIds.has(p.id));

        // Combine: exact matches first, then fuzzy
        baseProducts = [...exactMatches, ...fuzzyMatches];

        // Cache search result (limit cache size)
        if (this._searchCache.size >= MAX_SEARCH_CACHE_SIZE) {
          const firstKey = this._searchCache.keys().next().value;
          this._searchCache.delete(firstKey);
        }
        this._searchCache.set(searchTerm, baseProducts);
      }

      // Auto-switch to relevance only when search first becomes active
      if (!this._lastSearchWasActive && this.sort !== 'relevance') {
        this.previousSort = this.sort;
        this.sort = 'relevance';
      }
      sortBy = this.sort;
      this._lastSearchWasActive = true;
    } else {
      baseProducts = this.allProducts;

      // Restore previous sort when search cleared (only if still on relevance)
      if (this._lastSearchWasActive && this.sort === 'relevance') {
        this.sort = this.previousSort;
      }
      sortBy = this.sort;
      this._lastSearchWasActive = false;
    }

    // Apply additional filters
    this.filteredProducts = baseProducts.filter((product) => {
      if (this.category && product.category !== this.category) return false;
      if (this.selectedVendors.length > 0) {
        const hasVendor =
          product.vendors?.some((v) => this.selectedVendors.includes(v.name)) ?? false;
        if (!hasVendor) return false;
      }
      if (this.stock === 'instock' && !product.inStock) return false;
      if (this.minPrice && product.lowestPrice < this.minPrice) return false;
      if (this.maxPrice && product.lowestPrice > this.maxPrice) return false;
      return true;
    });

    // Apply sort (skip for relevance to preserve Fuse ranking)
    if (sortBy !== 'relevance') {
      this.filteredProducts.sort((a, b) => {
        switch (sortBy) {
          case 'discount-pct':
            return b._discountPercent - a._discountPercent;
          case 'discount-dollars':
            return b._discountDollars - a._discountDollars;
          case 'price-asc':
            return a.lowestPrice - b.lowestPrice;
          case 'price-desc':
            return b.lowestPrice - a.lowestPrice;
          case 'name-asc':
            return a.title.localeCompare(b.title);
          case 'name-desc':
            return b.title.localeCompare(a.title);
          default:
            return 0;
        }
      });
    }

    this.resetDisplay();
    this.updateURL();
  },

  // ===== DISPLAY CONTROL =====
  resetDisplay() {
    const perPage =
      this.perPage === 'all' ? this.filteredProducts.length : parseInt(this.perPage, 10);
    this.displayedCount = Math.min(perPage, this.filteredProducts.length);
  },

  loadMore() {
    const perPage =
      this.perPage === 'all' ? this.filteredProducts.length : parseInt(this.perPage, 10);
    this.displayedCount = Math.min(this.displayedCount + perPage, this.filteredProducts.length);
  },

  // ===== CALCULATIONS =====
  calculateBestDiscount(product, type = 'percent') {
    if (!product?.vendors?.length) return 0;

    // Only consider in-stock vendors for discount calculation
    // This ensures the displayed discount matches what customers can actually buy
    // Falls back to all vendors if none are in stock
    const inStockVendors = product.vendors.filter((v) => v.inStock);
    const vendorsToCheck = inStockVendors.length > 0 ? inStockVendors : product.vendors;

    let maxDiscount = 0;
    for (const vendor of vendorsToCheck) {
      if (!vendor.regularPrice || vendor.price >= vendor.regularPrice) continue;

      const discount =
        type === 'percent'
          ? ((vendor.regularPrice - vendor.price) / vendor.regularPrice) * 100
          : vendor.regularPrice - vendor.price;

      maxDiscount = Math.max(maxDiscount, discount);
    }
    return maxDiscount;
  },

  // Keep these for template compatibility (use pre-computed values)
  getDiscountPercent(product) {
    return product._discountPercent ?? 0;
  },

  getDiscountDollars(product) {
    return product._discountDollars ?? 0;
  },

  // ===== URL HANDLING =====
  loadFiltersFromURL() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('q')) this.search = params.get('q');
    if (params.get('category')) this.category = params.get('category');
    if (params.get('stores')) this.selectedVendors = params.get('stores').split(',');
    if (params.has('stock')) this.stock = params.get('stock');
    if (params.get('sort')) {
      this.sort = params.get('sort');
      this.previousSort = params.get('sort');
    }
    if (params.get('perPage')) this.perPage = params.get('perPage');
    if (params.get('showVendors')) this.showVendors = params.get('showVendors');
    if (params.get('searchTags') === 'true') this.searchTags = true;
    if (params.get('minPrice')) this.minPrice = parseFloat(params.get('minPrice'));
    if (params.get('maxPrice')) this.maxPrice = parseFloat(params.get('maxPrice'));
    if (params.get('view')) this.viewMode = params.get('view');
  },

  updateURL() {
    const params = new URLSearchParams();
    if (this.search.trim()) params.set('q', this.search.trim());
    if (this.category) params.set('category', this.category);
    if (this.selectedVendors.length > 0) params.set('stores', this.selectedVendors.join(','));
    if (this.stock) params.set('stock', this.stock);
    if (this.sort && this.sort !== 'relevance') params.set('sort', this.sort);
    if (this.perPage !== String(DEFAULT_PER_PAGE)) params.set('perPage', this.perPage);
    if (this.showVendors !== 'best') params.set('showVendors', this.showVendors);
    if (this.searchTags) params.set('searchTags', 'true');
    if (this.minPrice) params.set('minPrice', this.minPrice);
    if (this.maxPrice) params.set('maxPrice', this.maxPrice);
    if (this.viewMode !== 'card') params.set('view', this.viewMode);

    const url = params.toString() ? `?${params}` : window.location.pathname;
    history.replaceState(null, '', url);
  },

  // ===== UI INTERACTIONS =====
  clearFilters() {
    this.search = '';
    this.category = '';
    this.selectedVendors = [];
    this.stock = 'instock';
    this.minPrice = null;
    this.maxPrice = null;
    this.sort = 'discount-pct';
    this.searchTags = false;
  },

  toggleExpanded(productId) {
    this.expandedProducts[productId] = !this.expandedProducts[productId];
  },

  isExpanded(productId) {
    return !!this.expandedProducts[productId];
  },

  // ===== REFERRAL TRACKING =====
  addReferral(url) {
    if (!url || url === '#') return url;
    try {
      const u = new URL(url);
      u.searchParams.set('utm_source', 'gsau.gg');
      u.searchParams.set('utm_medium', 'referral');
      return u.toString();
    } catch {
      return url;
    }
  },

  trackStoreClick(storeName) {
    if (typeof gtag !== 'undefined') {
      gtag('event', 'store_click', {
        store_name: storeName,
      });
    }
  },

  // ===== NOTIFICATIONS =====
  showToast(message, type = 'info', action = null) {
    this.toast = { message, type, action };
    // Don't auto-dismiss if there's an action (user needs to interact or dismiss)
    if (!action) {
      setTimeout(() => {
        this.toast = null;
      }, TOAST_DURATION_MS);
    }
  },

  dismissToast() {
    this.toast = null;
  },
}));

// ========== STATUS APP COMPONENT ==========
Alpine.data('statusApp', () => ({
  // ===== STATE =====
  stats: null,
  loading: true,
  error: null,
  selectedStore: null,
  selectedStoreFiltered: null,

  // ===== COMPUTED =====
  get theme() {
    return this.$store.theme.current;
  },

  get stores() {
    if (!this.stats?.stores) return [];
    return [...this.stats.stores].sort((a, b) =>
      a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
    );
  },

  get errorCount() {
    return this.stats?.stores?.filter((s) => s.error).length ?? 0;
  },

  get totalFiltered() {
    return this.stats?.stores?.reduce((sum, s) => sum + s.filtered, 0) ?? 0;
  },

  // ===== LIFECYCLE =====
  async init() {
    this.$store.theme.init();
    await this.loadStats();
  },

  // ===== DATA LOADING =====
  async loadStats() {
    try {
      this.loading = true;
      const response = await this.fetchWithTimeout('./data/stats.json', FETCH_TIMEOUT_MS);
      if (!response.ok) throw new Error(`HTTP ${response.status}: Failed to load stats`);
      this.stats = await response.json();
    } catch (err) {
      console.error('Error loading stats:', err);
      this.error = err?.message ?? 'An unknown error occurred';
    } finally {
      this.loading = false;
    }
  },

  async fetchWithTimeout(url, timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
      return await fetch(url, { signal: controller.signal });
    } finally {
      clearTimeout(timeoutId);
    }
  },

  // ===== UTILITIES =====
  formatDate(dateString) {
    return new Date(dateString).toLocaleString();
  },

  formatCacheAge(dateString) {
    if (!dateString) return 'cached';
    const cacheTime = new Date(dateString);
    const now = new Date();
    const diffMs = now - cacheTime;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 60) return `cached ${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    return `cached ${diffHours}h ago`;
  },

  // ===== LOG MODAL =====
  showLogs(store) {
    this.selectedStore = store;
  },

  // ===== FILTERED PRODUCTS MODAL =====
  showFilteredProducts(store) {
    this.selectedStoreFiltered = store;
  },
}));

// ========== TRACKER APP COMPONENT ==========
Alpine.data('trackerApp', () => ({
  // ===== STATE =====
  trackerData: {},
  products: {},
  loading: true,
  error: null,

  // ===== COMPUTED =====
  get theme() {
    return this.$store.theme.current;
  },

  get cutoffTimestamp() {
    return Math.floor(Date.now() / 1000) - 24 * 60 * 60;
  },

  get priceChanges() {
    const changes = [];

    for (const [productId, history] of Object.entries(this.trackerData)) {
      const product = this.products[productId];
      if (!product) continue;

      // Process vendor-level changes
      if (history.vendors) {
        for (const [vendor, entries] of Object.entries(history.vendors)) {
          for (const entry of entries) {
            if (entry.prev !== undefined && entry.t >= this.cutoffTimestamp) {
              const vendorData = product.vendors?.find((v) => v.name === vendor);
              changes.push({
                id: `${productId}-${vendor}-${entry.t}`,
                type: 'price',
                productId,
                productTitle: product.title,
                productImage: product.image,
                productCategory: product.category,
                vendor,
                vendorUrl: vendorData?.url || '#',
                timestamp: entry.t,
                oldPrice: entry.prev,
                newPrice: entry.p,
                percentChange: ((entry.prev - entry.p) / entry.prev) * 100,
                direction: entry.prev > entry.p ? 'down' : 'up',
              });
            }
          }
        }
      }
    }

    return changes.sort((a, b) => b.timestamp - a.timestamp);
  },

  get newProducts() {
    const newItems = [];
    // Baseline: ignore products first seen before this (initial tracking load)
    const trackingBaseline = 1767013292; // 2025-12-29 - after initial production scrape

    for (const [productId, product] of Object.entries(this.products)) {
      const history = this.trackerData[productId];

      // No history = brand new (just added, not yet scraped into history)
      if (!history) {
        const firstVendor = product.vendors?.[0];
        newItems.push({
          id: `new-${productId}`,
          type: 'new',
          productId,
          productTitle: product.title,
          productImage: product.image,
          productCategory: product.category,
          vendor: firstVendor?.name || 'Unknown',
          vendorUrl: firstVendor?.url || '#',
          timestamp: Math.floor(Date.now() / 1000),
          price: product.lowestPrice,
          inStock: product.inStock,
        });
        continue;
      }

      // Find earliest timestamp in history
      let earliestTimestamp = Infinity;
      if (history.lowest?.length > 0) {
        earliestTimestamp = Math.min(earliestTimestamp, history.lowest[0].t);
      }
      if (history.vendors) {
        for (const entries of Object.values(history.vendors)) {
          if (entries.length > 0) {
            earliestTimestamp = Math.min(earliestTimestamp, entries[0].t);
          }
        }
      }

      // Show as "new" if first seen AFTER baseline AND within 24 hours
      if (
        earliestTimestamp > trackingBaseline &&
        earliestTimestamp >= this.cutoffTimestamp &&
        earliestTimestamp !== Infinity
      ) {
        const firstVendor = product.vendors?.[0];
        newItems.push({
          id: `new-${productId}`,
          type: 'new',
          productId,
          productTitle: product.title,
          productImage: product.image,
          productCategory: product.category,
          vendor: firstVendor?.name || 'Unknown',
          vendorUrl: firstVendor?.url || '#',
          timestamp: earliestTimestamp,
          price: product.lowestPrice,
          inStock: product.inStock,
        });
      }
    }

    return newItems.sort((a, b) => b.timestamp - a.timestamp);
  },

  get stockChanges() {
    const changes = [];
    // Baseline: ignore stock changes before stock tracking was deployed
    const stockBaseline = 1767149439; // 2025-12-31 - stock tracking deployment

    for (const [productId, history] of Object.entries(this.trackerData)) {
      const product = this.products[productId];
      if (!product) continue;

      for (const [vendor, entries] of Object.entries(history.vendors || {})) {
        for (const entry of entries) {
          if (
            entry.stockPrev !== undefined &&
            entry.t >= this.cutoffTimestamp &&
            entry.t > stockBaseline
          ) {
            const vendorData = product.vendors?.find((v) => v.name === vendor);
            changes.push({
              id: `stock-${productId}-${vendor}-${entry.t}`,
              type: entry.s ? 'back-in-stock' : 'out-of-stock',
              productId,
              productTitle: product.title,
              productImage: product.image,
              productCategory: product.category,
              vendor,
              vendorUrl: vendorData?.url || '#',
              timestamp: entry.t,
              price: entry.p,
            });
          }
        }
      }
    }
    return changes.sort((a, b) => b.timestamp - a.timestamp);
  },

  get allChanges() {
    // Combine price changes, stock changes, and new products, sorted by time
    return [...this.priceChanges, ...this.stockChanges, ...this.newProducts].sort(
      (a, b) => b.timestamp - a.timestamp,
    );
  },

  get stats() {
    return {
      drops: this.priceChanges.filter((c) => c.direction === 'down').length,
      increases: this.priceChanges.filter((c) => c.direction === 'up').length,
      newItems: this.newProducts.length,
      stockChanges: this.stockChanges.length,
    };
  },

  // ===== LIFECYCLE =====
  async init() {
    this.$store.theme.init();
    await this.loadData();
  },

  // ===== DATA LOADING =====
  async loadData() {
    try {
      this.loading = true;

      const [historyRes, productsRes] = await Promise.all([
        this.fetchWithTimeout('./data/tracker-data.json', FETCH_TIMEOUT_MS),
        this.fetchWithTimeout('./data/products.json', FETCH_TIMEOUT_MS),
      ]);

      if (!historyRes.ok) throw new Error('Failed to load price history');
      if (!productsRes.ok) throw new Error('Failed to load products');

      const historyData = await historyRes.json();
      const productsData = await productsRes.json();

      this.trackerData = historyData.history || {};

      // Build product lookup map by ID
      this.products = {};
      for (const p of productsData.products) {
        this.products[p.id] = p;
      }
    } catch (err) {
      console.error('Error loading data:', err);
      this.error = err?.message ?? 'An unknown error occurred';
    } finally {
      this.loading = false;
    }
  },

  async fetchWithTimeout(url, timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
      return await fetch(url, { signal: controller.signal });
    } finally {
      clearTimeout(timeoutId);
    }
  },

  // ===== UTILITIES =====
  formatRelativeTime(timestamp) {
    const seconds = Math.floor(Date.now() / 1000) - timestamp;
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  },

  formatDate(timestamp) {
    return new Date(timestamp * 1000).toLocaleString();
  },

  getProductSearchUrl(title) {
    return `index.html?q=${encodeURIComponent(title)}&stock=`;
  },

  // ===== REFERRAL TRACKING =====
  addReferral(url) {
    if (!url || url === '#') return url;
    try {
      const u = new URL(url);
      u.searchParams.set('utm_source', 'gsau.gg');
      u.searchParams.set('utm_medium', 'referral');
      return u.toString();
    } catch {
      return url;
    }
  },

  trackStoreClick(storeName) {
    if (typeof gtag !== 'undefined') {
      gtag('event', 'store_click', {
        store_name: storeName,
      });
    }
  },
}));

// ========== START ALPINE ==========
Alpine.start();
