<script lang="ts">
	import ThemeToggle from './ThemeToggle.svelte';
	import { page } from '$app/stores';
	import { filters } from '$lib/stores/filters.svelte';
	import { goto } from '$app/navigation';

	interface NavItem {
		href: string;
		label: string;
	}

	const navItems: NavItem[] = [
		{ href: '/', label: 'Products' },
		{ href: '/tracker', label: 'Tracker' },
		{ href: '/map', label: 'Map' },
		{ href: '/status', label: 'Status' },
		{ href: '/about', label: 'About' }
	];

	// Use $derived with store subscription for path
	const currentPath = $derived($page.url.pathname);

	let searchInput = $state(filters.value.search);
	let debounceTimer: ReturnType<typeof setTimeout> | null = null;
	let mobileSearchOpen = $state(false);
	let mobileSearchInput: HTMLInputElement | null = $state(null);
	let desktopSearchInput: HTMLInputElement | null = $state(null);

	// Global keyboard shortcut: "/" to focus search
	function handleGlobalKeydown(e: KeyboardEvent) {
		// Ignore if user is typing in an input/textarea
		if (
			e.target instanceof HTMLInputElement ||
			e.target instanceof HTMLTextAreaElement ||
			(e.target as HTMLElement)?.isContentEditable
		) {
			return;
		}

		if (e.key === '/') {
			e.preventDefault();
			desktopSearchInput?.focus();
		}
	}

	// Keep search input in sync with filters (e.g., after navigation)
	$effect(() => {
		searchInput = filters.value.search;
	});

	// Auto-focus mobile search input when opened
	$effect(() => {
		if (mobileSearchOpen && mobileSearchInput) {
			mobileSearchInput.focus();
		}
	});

	// Cleanup debounce timer on component destroy
	$effect(() => {
		return () => {
			if (debounceTimer) {
				clearTimeout(debounceTimer);
			}
		};
	});

	function handleSearch(e: Event) {
		const value = (e.target as HTMLInputElement).value;
		searchInput = value;

		// Clear pending debounce
		if (debounceTimer) clearTimeout(debounceTimer);

		if (currentPath === '/') {
			// On products page: debounce filter updates (150ms)
			debounceTimer = setTimeout(() => {
				filters.setSearch(value);
			}, 150);
		} else {
			// On other pages: debounce navigation (300ms)
			debounceTimer = setTimeout(() => {
				goto(value ? `/?q=${encodeURIComponent(value)}` : '/');
			}, 300);
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			if (mobileSearchOpen) {
				mobileSearchOpen = false;
			} else {
				searchInput = '';
				filters.setSearch('');
				(e.target as HTMLInputElement).blur();
			}
		} else if (e.key === 'Enter' && currentPath !== '/') {
			// Navigate immediately on Enter
			if (debounceTimer) clearTimeout(debounceTimer);
			goto(searchInput ? `/?q=${encodeURIComponent(searchInput)}` : '/');
			mobileSearchOpen = false;
		}
	}

	function clearSearch() {
		searchInput = '';
		filters.setSearch('');
	}

	function closeMobileSearch() {
		mobileSearchOpen = false;
	}
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<header
	class="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
>
	<div class="container mx-auto flex h-14 items-center px-4">
		<!-- Logo -->
		<a href="/" class="mr-6 flex items-center space-x-2">
			<span class="text-xl font-bold text-primary">GSAU.gg</span>
		</a>

		<!-- Desktop Navigation -->
		<nav class="hidden flex-1 items-center space-x-6 md:flex">
			{#each navItems as item}
				<a
					href={item.href}
					class="text-sm font-medium transition-colors hover:text-primary {currentPath === item.href
						? 'text-primary'
						: 'text-muted-foreground'}"
				>
					{item.label}
				</a>
			{/each}
		</nav>

		<!-- Right side: Search + Discord + Theme toggle -->
		<div class="flex flex-1 items-center justify-end space-x-2 sm:space-x-4">
			<!-- Desktop Search -->
			<div class="hidden w-full max-w-sm lg:block">
				<div
					class="flex h-9 w-full items-center rounded-md border border-input bg-background px-3 text-sm focus-within:border-primary focus-within:ring-1 focus-within:ring-primary"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="16"
						height="16"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="mr-2 text-muted-foreground"
					>
						<circle cx="11" cy="11" r="8" />
						<path d="m21 21-4.3-4.3" />
					</svg>
					<input
						bind:this={desktopSearchInput}
						id="desktop-search"
						name="search"
						type="text"
						placeholder="Search products..."
						aria-label="Search products"
						value={searchInput}
						oninput={handleSearch}
						onkeydown={handleKeydown}
						class="flex-1 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none"
					/>
					{#if searchInput}
						<button
							onclick={clearSearch}
							class="ml-2 text-muted-foreground hover:text-foreground"
							aria-label="Clear search"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="14"
								height="14"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<path d="M18 6 6 18" />
								<path d="m6 6 12 12" />
							</svg>
						</button>
					{:else}
						<kbd
							class="ml-2 hidden rounded border border-border bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground sm:inline-block"
							aria-hidden="true">/</kbd
						>
					{/if}
				</div>
			</div>

			<!-- Discord link - visible on all sizes, smaller on mobile -->
			<a
				href="https://discord.gg/rmfZtWD95f"
				target="_blank"
				rel="noopener"
				class="flex h-8 w-8 items-center justify-center rounded-md text-[#5865F2] transition-colors hover:bg-[#5865F2]/10 hover:text-[#4752C4] sm:h-9 sm:w-9"
				aria-label="Join Discord"
				title="Join Gelsoft AU Discord"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5"
					viewBox="0 0 24 24"
					fill="currentColor"
				>
					<path
						d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"
					/>
				</svg>
			</a>

			<ThemeToggle />

			<!-- Mobile search button (replaces hamburger) -->
			<button
				onclick={() => (mobileSearchOpen = !mobileSearchOpen)}
				class="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-background text-foreground transition-colors hover:bg-muted sm:h-9 sm:w-9 lg:hidden"
				aria-label={mobileSearchOpen ? 'Close search' : 'Open search'}
				aria-expanded={mobileSearchOpen}
			>
				{#if mobileSearchOpen}
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="18"
						height="18"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<path d="M18 6 6 18" />
						<path d="m6 6 12 12" />
					</svg>
				{:else}
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="18"
						height="18"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
					>
						<circle cx="11" cy="11" r="8" />
						<path d="m21 21-4.3-4.3" />
					</svg>
				{/if}
			</button>
		</div>
	</div>

	<!-- Mobile search overlay -->
	{#if mobileSearchOpen}
		<!-- Backdrop -->
		<button
			class="fixed inset-0 top-14 z-40 bg-black/20 backdrop-blur-sm lg:hidden"
			onclick={closeMobileSearch}
			aria-label="Close search"
			tabindex="-1"
		></button>

		<!-- Search bar -->
		<div
			class="absolute inset-x-0 top-14 z-50 border-b border-border bg-background px-4 py-3 shadow-lg lg:hidden"
			style="animation: slideDown 200ms ease-out"
		>
			<div
				class="flex h-10 w-full items-center rounded-md border border-input bg-background px-3 text-sm focus-within:border-primary focus-within:ring-1 focus-within:ring-primary"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="mr-2 shrink-0 text-muted-foreground"
				>
					<circle cx="11" cy="11" r="8" />
					<path d="m21 21-4.3-4.3" />
				</svg>
				<input
					bind:this={mobileSearchInput}
					id="mobile-search"
					name="search"
					type="text"
					placeholder="Search products..."
					aria-label="Search products"
					value={searchInput}
					oninput={handleSearch}
					onkeydown={handleKeydown}
					class="flex-1 bg-transparent text-base text-foreground placeholder:text-muted-foreground focus:outline-none"
				/>
				{#if searchInput}
					<button
						onclick={clearSearch}
						class="ml-2 shrink-0 text-muted-foreground hover:text-foreground"
						aria-label="Clear search"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<path d="M18 6 6 18" />
							<path d="m6 6 12 12" />
						</svg>
					</button>
				{/if}
			</div>
		</div>
	{/if}
</header>

<style>
	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
