import Alpine from 'alpinejs';

// ========== THEME STORE (minimal for pages that only need theming) ==========
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

// Start Alpine
Alpine.start();
