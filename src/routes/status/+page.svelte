<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import { dataProvider } from '$lib/data/static';
	import type { StoreStats, LogEntry } from '$lib/data/types';
	import { addUtmParams, trackStoreClick } from '$lib/utils/format';
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Collapsible from '$lib/components/ui/collapsible';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import FileText from '@lucide/svelte/icons/file-text';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import Loader2 from '@lucide/svelte/icons/loader-2';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import CircleAlert from '@lucide/svelte/icons/circle-alert';
	import Clock from '@lucide/svelte/icons/clock';

	// Fetch stats data
	const stats = createQuery(() => ({
		queryKey: ['stats'] as const,
		queryFn: () => dataProvider.getStats(),
		staleTime: 1000 * 60 * 5 // 5 minutes
	}));

	// Calculate totals from stores
	const totals = $derived.by(() => {
		if (!stats.data?.stores)
			return { fetched: 0, filtered: 0, final: 0, inStock: 0, outOfStock: 0 };
		return stats.data.stores.reduce(
			(acc, store) => ({
				fetched: acc.fetched + store.fetched,
				filtered: acc.filtered + store.filtered,
				final: acc.final + store.final,
				inStock: acc.inStock + store.inStock,
				outOfStock: acc.outOfStock + store.outOfStock
			}),
			{ fetched: 0, filtered: 0, final: 0, inStock: 0, outOfStock: 0 }
		);
	});

	// Group stores by status, each group sorted alphabetically
	const storeGroups = $derived.by(() => {
		if (!stats.data?.stores) return { errors: [], cached: [], healthy: [] };

		const errors: StoreStats[] = [];
		const cached: StoreStats[] = [];
		const healthy: StoreStats[] = [];

		for (const store of stats.data.stores) {
			if (store.error) {
				errors.push(store);
			} else if (store.cached_at) {
				cached.push(store);
			} else {
				healthy.push(store);
			}
		}

		const sortAlpha = (a: StoreStats, b: StoreStats) => a.name.localeCompare(b.name);
		return {
			errors: errors.sort(sortAlpha),
			cached: cached.sort(sortAlpha),
			healthy: healthy.sort(sortAlpha)
		};
	});

	// Collapsible state
	let errorsOpen = $state(true);
	let cachedOpen = $state(true);
	let healthyOpen = $state(true);

	// Modal state for log viewing
	let selectedStore = $state<StoreStats | null>(null);
	let showLogs = $state(false);

	function openLogs(store: StoreStats) {
		selectedStore = store;
		showLogs = true;
	}

	function closeLogs() {
		showLogs = false;
		selectedStore = null;
	}

	// Format duration
	function formatDuration(seconds: number): string {
		if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
		if (seconds < 60) return `${seconds.toFixed(1)}s`;
		return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
	}

	// Format relative time
	function formatRelativeTime(dateString: string): string {
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffMins = Math.floor(diffMs / (1000 * 60));
		const diffHours = Math.floor(diffMins / 60);

		if (diffMins < 1) return 'Just now';
		if (diffMins < 60) return `${diffMins}m ago`;
		if (diffHours < 24) return `${diffHours}h ago`;
		return `${Math.floor(diffHours / 24)}d ago`;
	}

	// Staleness status: green <3h, yellow 3-12h, red >12h
	const staleness = $derived.by(() => {
		if (!stats.data?.lastUpdated) return 'fresh';
		const date = new Date(stats.data.lastUpdated);
		const now = new Date();
		const diffHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

		if (diffHours < 3) return 'fresh';
		if (diffHours < 12) return 'stale';
		return 'old';
	});
</script>

<svelte:head>
	<title>Scraper Status - GSAU.gg</title>
	<meta
		name="description"
		content="Monitor store scraper health and logs. Real-time monitoring of gel blaster store data collection."
	/>
	<link rel="canonical" href="https://www.gsau.gg/status" />
	<meta property="og:title" content="Scraper Status - GSAU.gg" />
	<meta
		property="og:description"
		content="Real-time monitoring of store data collection for gel blaster retailers."
	/>
	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://www.gsau.gg/status" />
</svelte:head>

<div class="space-y-4 sm:space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-xl sm:text-2xl font-bold tracking-tight">Scraper Status</h1>
		<p class="text-sm text-muted-foreground">Real-time monitoring of store data collection</p>
	</div>

	{#if stats.isLoading}
		<div class="flex items-center gap-2 text-muted-foreground">
			<Loader2 class="h-5 w-5 animate-spin" />
			<span>Loading status data...</span>
		</div>
	{:else if stats.isError}
		<div class="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
			<p class="font-medium">Error loading status data</p>
			<p class="text-sm">{stats.error?.message}</p>
		</div>
	{:else if stats.data}
		<!-- Hero Metrics Bar -->
		<div class="rounded-lg border-2 border-border bg-muted/30 p-4">
			<div class="flex flex-wrap items-center justify-between gap-4">
				<!-- Primary metrics -->
				<div class="flex flex-wrap items-baseline gap-6 sm:gap-10">
					<div>
						<span class="font-mono text-3xl font-bold tracking-tight tabular-nums"
							>{totals.final.toLocaleString()}</span
						>
						<span class="ml-2 text-sm text-muted-foreground">products</span>
					</div>
					<div>
						<span class="font-mono text-3xl font-bold tracking-tight tabular-nums"
							>{stats.data.stores.length}</span
						>
						<span class="ml-2 text-sm text-muted-foreground">stores</span>
					</div>
					<div>
						<span class="font-mono text-3xl font-bold tracking-tight tabular-nums"
							>{formatDuration(stats.data.duration)}</span
						>
						<span class="ml-2 text-sm text-muted-foreground">duration</span>
					</div>
				</div>

				<!-- Status indicator -->
				<Tooltip.Root>
					<Tooltip.Trigger>
						<div
							class="flex items-center gap-2 rounded-full bg-background px-4 py-2 shadow-sm ring-1 ring-border"
						>
							<span class="relative flex h-2 w-2">
								{#if staleness === 'fresh'}
									<span
										class="absolute inline-flex h-full w-full animate-ping rounded-full bg-stock-available opacity-75"
									></span>
									<span class="relative inline-flex h-2 w-2 rounded-full bg-stock-available"></span>
								{:else if staleness === 'stale'}
									<span class="relative inline-flex h-2 w-2 rounded-full bg-price-rise"></span>
								{:else}
									<span class="relative inline-flex h-2 w-2 rounded-full bg-destructive"></span>
								{/if}
							</span>
							<span class="text-sm font-medium">
								<span
									class={staleness === 'fresh'
										? 'text-stock-available'
										: staleness === 'stale'
											? 'text-price-rise'
											: 'text-destructive'}
								>
									{staleness === 'fresh' ? 'Fresh' : staleness === 'stale' ? 'Stale' : 'Outdated'}
								</span>
								<span class="text-muted-foreground">•</span>
								{formatRelativeTime(stats.data.lastUpdated)}
							</span>
						</div>
					</Tooltip.Trigger>
					<Tooltip.Content>
						{new Date(stats.data.lastUpdated).toLocaleString()}
					</Tooltip.Content>
				</Tooltip.Root>
			</div>

			<!-- Secondary stats -->
			<div class="mt-3 flex flex-wrap gap-4 text-sm text-muted-foreground">
				<span>{totals.inStock.toLocaleString()} in stock</span>
				<span>•</span>
				<span>{totals.filtered.toLocaleString()} filtered</span>
				<span>•</span>
				<span class="text-stock-available">{storeGroups.healthy.length} healthy</span>
				<span>•</span>
				<span class="text-price-rise">{storeGroups.cached.length} cached</span>
				{#if storeGroups.errors.length > 0}
					<span>•</span>
					<span class="text-destructive">{storeGroups.errors.length} errors</span>
				{/if}
			</div>
		</div>

		<!-- Store sections -->
		<div class="space-y-4">
			<!-- Errors Section -->
			{#if storeGroups.errors.length > 0}
				<Collapsible.Root bind:open={errorsOpen}>
					<Collapsible.Trigger
						class="flex w-full items-center gap-3 rounded-lg border-2 border-destructive/30 bg-destructive/5 px-4 py-3 text-left hover:bg-destructive/10"
					>
						<CircleAlert class="h-5 w-5 text-destructive" />
						<span class="flex-1 font-semibold text-destructive">Errors</span>
						<Badge variant="destructive">{storeGroups.errors.length}</Badge>
						<ChevronDown
							class="h-4 w-4 text-destructive transition-transform duration-200 {errorsOpen
								? 'rotate-180'
								: ''}"
						/>
					</Collapsible.Trigger>
					<Collapsible.Content>
						<div class="mt-2 space-y-1">
							{#each storeGroups.errors as store, i (store.name)}
								<button
									onclick={() => openLogs(store)}
									class="group flex w-full items-center gap-3 border-l-4 bg-background px-4 py-3 text-left transition-all duration-200 hover:bg-muted/50 focus-visible:ring-border animate-in fade-in slide-in-from-left-2"
									style="border-color: var(--status-error); animation-delay: {i *
										30}ms; animation-fill-mode: backwards;"
								>
									<div class="min-w-0 flex-1">
										<div class="flex items-center gap-2">
											<span class="font-medium">{store.name}</span>
											<Badge variant="outline" class="text-xs">{store.platform}</Badge>
										</div>
										<p class="mt-1 truncate text-sm text-destructive">{store.error}</p>
									</div>
									<Tooltip.Root>
										<Tooltip.Trigger class="cursor-pointer">
											<FileText class="h-4 w-4 shrink-0 text-muted-foreground" />
										</Tooltip.Trigger>
										<Tooltip.Content>View logs</Tooltip.Content>
									</Tooltip.Root>
								</button>
							{/each}
						</div>
					</Collapsible.Content>
				</Collapsible.Root>
			{/if}

			<!-- Cached Section -->
			{#if storeGroups.cached.length > 0}
				<Collapsible.Root bind:open={cachedOpen}>
					<Collapsible.Trigger
						class="flex w-full items-center gap-3 rounded-lg border border-border bg-muted/30 px-4 py-3 text-left hover:bg-muted/50"
					>
						<Clock class="h-5 w-5 text-price-rise" />
						<span class="flex-1 font-semibold">Cached</span>
						<Badge variant="secondary">{storeGroups.cached.length}</Badge>
						<ChevronDown
							class="h-4 w-4 text-muted-foreground transition-transform duration-200 {cachedOpen
								? 'rotate-180'
								: ''}"
						/>
					</Collapsible.Trigger>
					<Collapsible.Content>
						<div class="mt-2 space-y-1">
							{#each storeGroups.cached as store, i (store.name)}
								<button
									onclick={() => openLogs(store)}
									class="group flex w-full items-center gap-3 border-l-4 bg-background px-4 py-3 text-left transition-all duration-200 hover:bg-muted/50 focus-visible:ring-border animate-in fade-in slide-in-from-left-2"
									style="border-color: var(--status-warning); animation-delay: {i *
										30}ms; animation-fill-mode: backwards;"
								>
									<div class="min-w-0 flex-1">
										<div class="flex items-center gap-2">
											<span class="font-medium">{store.name}</span>
											<Badge variant="outline" class="text-xs">{store.platform}</Badge>
											<span class="text-xs text-muted-foreground">
												cached {formatRelativeTime(store.cached_at!)}
											</span>
										</div>
										<div
											class="mt-1.5 flex flex-wrap items-center gap-x-1 gap-y-1 text-xs text-muted-foreground"
										>
											<span
												><span class="font-mono font-medium text-foreground"
													>{store.final.toLocaleString()}</span
												> products</span
											>
											<span class="text-border">•</span>
											<span
												><span class="font-mono font-medium"
													>{Math.round((store.inStock / store.final) * 100)}%</span
												> in stock</span
											>
											{#if store.filtered > 0}
												<span class="text-border">•</span>
												<span
													><span class="font-mono font-medium">{store.filtered}</span> filtered</span
												>
											{/if}
										</div>
									</div>
									<div class="flex shrink-0 items-center gap-2">
										<a
											href={addUtmParams(store.url)}
											target="_blank"
											rel="noopener noreferrer"
											onclick={(e) => {
												e.stopPropagation();
												trackStoreClick(store.name);
											}}
											class="rounded p-1.5 text-muted-foreground opacity-50 transition-opacity hover:bg-muted hover:text-foreground hover:opacity-100"
										>
											<ExternalLink class="h-4 w-4" />
										</a>
										<Tooltip.Root>
											<Tooltip.Trigger class="cursor-pointer">
												<FileText class="h-4 w-4 text-muted-foreground" />
											</Tooltip.Trigger>
											<Tooltip.Content>View logs</Tooltip.Content>
										</Tooltip.Root>
									</div>
								</button>
							{/each}
						</div>
					</Collapsible.Content>
				</Collapsible.Root>
			{/if}

			<!-- Healthy Section -->
			{#if storeGroups.healthy.length > 0}
				<Collapsible.Root bind:open={healthyOpen}>
					<Collapsible.Trigger
						class="flex w-full items-center gap-3 rounded-lg border border-border bg-muted/30 px-4 py-3 text-left hover:bg-muted/50"
					>
						<CircleCheck class="h-5 w-5 text-stock-available" />
						<span class="flex-1 font-semibold">Healthy</span>
						<Badge variant="secondary">{storeGroups.healthy.length}</Badge>
						<ChevronDown
							class="h-4 w-4 text-muted-foreground transition-transform duration-200 {healthyOpen
								? 'rotate-180'
								: ''}"
						/>
					</Collapsible.Trigger>
					<Collapsible.Content>
						<div class="mt-2 space-y-1">
							{#each storeGroups.healthy as store, i (store.name)}
								<button
									onclick={() => openLogs(store)}
									class="group flex w-full items-center gap-3 border-l-4 bg-background px-4 py-3 text-left transition-all duration-200 hover:bg-muted/50 focus-visible:ring-border animate-in fade-in slide-in-from-left-2"
									style="border-color: var(--status-success); animation-delay: {i *
										30}ms; animation-fill-mode: backwards;"
								>
									<div class="min-w-0 flex-1">
										<div class="flex items-center gap-2">
											<span class="font-medium">{store.name}</span>
											<Badge variant="outline" class="text-xs">{store.platform}</Badge>
											<span class="text-xs text-muted-foreground">
												{formatDuration(store.duration)}
											</span>
										</div>
										<div
											class="mt-1.5 flex flex-wrap items-center gap-x-1 gap-y-1 text-xs text-muted-foreground"
										>
											<span
												><span class="font-mono font-medium text-foreground"
													>{store.final.toLocaleString()}</span
												> products</span
											>
											<span class="text-border">•</span>
											<span
												><span class="font-mono font-medium"
													>{Math.round((store.inStock / store.final) * 100)}%</span
												> in stock</span
											>
											{#if store.filtered > 0}
												<span class="text-border">•</span>
												<span
													><span class="font-mono font-medium">{store.filtered}</span> filtered</span
												>
											{/if}
										</div>
									</div>
									<div class="flex shrink-0 items-center gap-2">
										<a
											href={addUtmParams(store.url)}
											target="_blank"
											rel="noopener noreferrer"
											onclick={(e) => {
												e.stopPropagation();
												trackStoreClick(store.name);
											}}
											class="rounded p-1.5 text-muted-foreground opacity-50 transition-opacity hover:bg-muted hover:text-foreground hover:opacity-100"
										>
											<ExternalLink class="h-4 w-4" />
										</a>
										<Tooltip.Root>
											<Tooltip.Trigger class="cursor-pointer">
												<FileText class="h-4 w-4 text-muted-foreground" />
											</Tooltip.Trigger>
											<Tooltip.Content>View logs</Tooltip.Content>
										</Tooltip.Root>
									</div>
								</button>
							{/each}
						</div>
					</Collapsible.Content>
				</Collapsible.Root>
			{/if}

			<!-- All healthy message -->
			{#if storeGroups.errors.length === 0 && storeGroups.cached.length === 0}
				<div
					class="flex items-center gap-3 rounded-lg border-2 border-stock-available/30 bg-stock-available/5 px-4 py-3"
				>
					<CircleCheck class="h-5 w-5 text-stock-available" />
					<span class="font-medium text-stock-available"
						>All {stats.data.stores.length} stores are healthy</span
					>
				</div>
			{/if}
		</div>
	{/if}
</div>

<!-- Log viewer dialog -->
<Dialog.Root bind:open={showLogs} onOpenChange={(open) => !open && closeLogs()}>
	<Dialog.Content
		class="max-h-[85vh] w-[95vw] max-w-2xl gap-0 overflow-hidden rounded-lg border-2 border-border bg-background p-0 shadow-2xl"
	>
		{#if selectedStore}
			<!-- Header with stats grid -->
			<div class="border-b-2 border-border bg-muted/30 px-5 py-4">
				<Dialog.Title class="text-xl font-bold tracking-tight">
					{selectedStore.name}
				</Dialog.Title>
				<Dialog.Description class="sr-only">Store scraper details and logs</Dialog.Description>

				<!-- Stats row -->
				<div class="mt-3 flex flex-wrap gap-2">
					<div
						class="flex items-center gap-1.5 rounded-full bg-background px-3 py-1 text-sm font-medium shadow-sm ring-1 ring-border"
					>
						<span class="text-muted-foreground">Products</span>
						<span class="font-mono">{selectedStore.final.toLocaleString()}</span>
					</div>
					{#if selectedStore.filteredProducts?.length}
						<div
							class="flex items-center gap-1.5 rounded-full bg-background px-3 py-1 text-sm font-medium shadow-sm ring-1 ring-border"
						>
							<span class="text-muted-foreground">Filtered</span>
							<span class="font-mono text-price-rise">{selectedStore.filteredProducts.length}</span>
						</div>
					{/if}
					<div
						class="flex items-center gap-1.5 rounded-full bg-background px-3 py-1 text-sm font-medium shadow-sm ring-1 ring-border"
					>
						<span class="text-muted-foreground">Duration</span>
						<span class="font-mono">{formatDuration(selectedStore.duration)}</span>
					</div>
					{#if selectedStore.error}
						<div
							class="flex items-center gap-1.5 rounded-full bg-destructive/10 px-3 py-1 text-sm font-medium text-destructive ring-1 ring-destructive/30"
						>
							Error
						</div>
					{/if}
				</div>
			</div>

			<!-- Logs section - terminal style -->
			<div class="border-b border-border px-5 py-4">
				<h3 class="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
					Logs
				</h3>
				{#if selectedStore.logs.length === 0}
					<p class="py-2 text-sm italic text-muted-foreground">No logs recorded</p>
				{:else}
					<div class="space-y-1 rounded-md bg-muted/40 p-2">
						{#each selectedStore.logs as log}
							<div
								class="flex items-start gap-3 rounded border-l-[3px] bg-background px-3 py-2 font-mono text-sm shadow-sm {log.level ===
								'ERROR'
									? 'border-l-destructive'
									: log.level === 'WARNING'
										? 'border-l-price-rise'
										: 'border-l-stock-available'}"
							>
								<span
									class="shrink-0 text-xs font-bold {log.level === 'ERROR'
										? 'text-destructive'
										: log.level === 'WARNING'
											? 'text-price-rise'
											: 'text-stock-available'}"
								>
									{log.level}
								</span>
								<span class="break-all text-foreground/90">{log.message}</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Filtered products - grouped by keyword -->
			{#if selectedStore.filteredProducts && selectedStore.filteredProducts.length > 0}
				{@const groupedProducts = selectedStore.filteredProducts.reduce(
					(acc, p) => {
						const key = p.keyword;
						if (!acc[key]) acc[key] = { reason: p.reason, items: [] };
						acc[key].items.push(p.title);
						return acc;
					},
					{} as Record<string, { reason: string; items: string[] }>
				)}
				<div class="max-h-[35vh] overflow-y-auto px-5 py-4">
					<h3 class="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
						Filtered Products
						<span class="ml-1 font-mono text-foreground"
							>{selectedStore.filteredProducts.length}</span
						>
					</h3>
					<div class="space-y-2">
						{#each Object.entries(groupedProducts) as [keyword, group]}
							<details class="group rounded-md border border-border bg-muted/20">
								<summary
									class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm hover:bg-muted/40"
								>
									<svg
										class="h-3 w-3 shrink-0 text-muted-foreground transition-transform group-open:rotate-90"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M9 5l7 7-7 7"
										/>
									</svg>
									<span
										class="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-muted-foreground"
									>
										{group.reason}
									</span>
									<span class="font-medium">{keyword}</span>
									<span class="ml-auto font-mono text-xs text-muted-foreground">
										{group.items.length}
									</span>
								</summary>
								<div class="border-t border-border bg-background/50 px-3 py-2">
									<ul class="space-y-1 text-sm text-muted-foreground">
										{#each group.items as title}
											<li class="truncate pl-5" {title}>• {title}</li>
										{/each}
									</ul>
								</div>
							</details>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</Dialog.Content>
</Dialog.Root>
