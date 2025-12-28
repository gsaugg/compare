import Alpine from 'alpinejs';
import Fuse from 'fuse.js';

// ========== CONSTANTS ==========
const TOAST_DURATION_MS = 5000;
const FUSE_THRESHOLD = 0.2;
const DEFAULT_PER_PAGE = 60;
const FETCH_TIMEOUT_MS = 10000;
const MAX_SEARCH_CACHE_SIZE = 10;

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

    // Setup keyboard shortcuts
    this.setupKeyboardShortcuts();

    // Load products
    await this.loadProducts();

    // Setup infinite scroll
    this.setupInfiniteScroll();
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
      this.allProducts = data.products.map((p) => ({
        ...p,
        _vendorNames: p.vendors?.map((v) => v.name).join(' ') ?? '',
        _discountPercent: this.calculateBestDiscount(p, 'percent'),
        _discountDollars: this.calculateBestDiscount(p, 'dollars'),
      }));

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
      const response = await fetch(url, { signal: controller.signal });
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

  // ===== SEARCH INDEX =====
  rebuildFuseIndex() {
    const keys = [
      { name: 'title', weight: 3.0 },
      { name: 'category', weight: 0.5 },
      { name: '_vendorNames', weight: 0.3 },
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
    const searchTerm = this.search.trim();
    let sortBy = this.sort;
    let baseProducts;

    if (searchTerm && this.fuse) {
      // Check search cache first
      if (this._searchCache.has(searchTerm)) {
        baseProducts = this._searchCache.get(searchTerm);
      } else {
        const results = this.fuse.search(searchTerm);
        baseProducts = results.map((r) => r.item);

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
      if (!vendor.comparePrice || vendor.price >= vendor.comparePrice) continue;

      const discount =
        type === 'percent'
          ? ((vendor.comparePrice - vendor.price) / vendor.comparePrice) * 100
          : vendor.comparePrice - vendor.price;

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
    if (params.get('stock')) this.stock = params.get('stock');
    if (params.get('sort')) {
      this.sort = params.get('sort');
      this.previousSort = params.get('sort');
    }
    if (params.get('perPage')) this.perPage = params.get('perPage');
    if (params.get('showVendors')) this.showVendors = params.get('showVendors');
    if (params.get('searchTags') === 'true') this.searchTags = true;
    if (params.get('minPrice')) this.minPrice = parseFloat(params.get('minPrice'));
    if (params.get('maxPrice')) this.maxPrice = parseFloat(params.get('maxPrice'));
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

  // ===== NOTIFICATIONS =====
  showToast(message, type = 'info') {
    this.toast = { message, type };
    setTimeout(() => {
      this.toast = null;
    }, TOAST_DURATION_MS);
  },
}));

// ========== STATUS APP COMPONENT ==========
Alpine.data('statusApp', () => ({
  // ===== STATE =====
  stats: null,
  loading: true,
  error: null,
  selectedStore: null,

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

  // ===== LOG MODAL =====
  showLogs(store) {
    this.selectedStore = store;
  },
}));

// ========== START ALPINE ==========
Alpine.start();
