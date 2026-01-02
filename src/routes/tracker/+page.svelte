<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import { dataProvider } from '$lib/data/static';
	import type { Item, PricePoint } from '$lib/data/types';
	import { formatPrice, addUtmParams, trackStoreClick } from '$lib/utils/format';
	import PriceSparkline from '$lib/components/product/PriceSparkline.svelte';
	import { Separator } from '$lib/components/ui/separator';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import * as Alert from '$lib/components/ui/alert';

	// Fetch items and item history
	const items = createQuery(() => ({
		queryKey: ['items'] as const,
		queryFn: () => dataProvider.getItems(),
		staleTime: 1000 * 60 * 60
	}));

	const itemHistory = createQuery(() => ({
		queryKey: ['itemHistory'] as const,
		queryFn: () => dataProvider.getItemHistory(),
		staleTime: 1000 * 60 * 60
	}));

	// Baselines - ignore data before these timestamps (initial tracking load)
	const TRACKING_BASELINE = 1767013292; // 2025-12-29 - after initial production scrape
	const STOCK_BASELINE = 1767151574; // 2025-12-31 13:26:14 - after initial bulk stock detection

	// Time filter options
	type TimeFilter = '24h' | '7d' | '30d';
	let timeFilter = $state<TimeFilter>('24h');

	// Event type filter
	type EventType =
		| 'all'
		| 'new'
		| 'price_drop'
		| 'price_increase'
		| 'back_in_stock'
		| 'out_of_stock';
	let eventFilter = $state<EventType>('all');

	const timeFilterMs = $derived(
		{
			'24h': 24 * 60 * 60 * 1000,
			'7d': 7 * 24 * 60 * 60 * 1000,
			'30d': 30 * 24 * 60 * 60 * 1000
		}[timeFilter]
	);

	// Unified feed item interface
	interface FeedItem {
		type: 'new' | 'price_drop' | 'price_increase' | 'back_in_stock' | 'out_of_stock';
		item: Item;
		timestamp: number;
		currentPrice: number;
		previousPrice?: number;
		percentChange?: number;
		regularPrice?: number;
		previousRegularPrice?: number;
		history: PricePoint[];
	}

	// Build unified feed from item-level data
	const feed = $derived.by(() => {
		if (!itemHistory.data?.history || !items.data?.items) return [];

		const now = Date.now();
		const cutoff = now - timeFilterMs;
		const feedItems: FeedItem[] = [];
		const seenItems = new Set<string>();

		for (const [itemId, history] of Object.entries(itemHistory.data.history)) {
			const item = items.data.items[itemId];
			if (!item) continue;

			if (!history || history.length === 0) continue;

			const sorted = [...history].sort((a, b) => b.t - a.t);

			// Check if this is a new item (only one history entry, first seen recently)
			if (sorted.length === 1) {
				const entry = sorted[0];
				const timestampSec = entry.t > 1e12 ? entry.t / 1000 : entry.t;
				const timestamp = entry.t > 1e12 ? entry.t : entry.t * 1000;

				if (timestampSec >= TRACKING_BASELINE && timestamp >= cutoff) {
					const key = `${itemId}-new`;
					if (!seenItems.has(key)) {
						seenItems.add(key);
						feedItems.push({
							type: 'new',
							item,
							timestamp,
							currentPrice: entry.p,
							regularPrice: entry.rp,
							history: sorted
						});
					}
				}
				continue;
			}

			// Check for changes between entries
			for (let i = 0; i < sorted.length - 1; i++) {
				const current = sorted[i];
				const previous = sorted[i + 1];
				const timestampSec = current.t > 1e12 ? current.t / 1000 : current.t;
				const timestamp = current.t > 1e12 ? current.t : current.t * 1000;

				// Skip if outside time filter
				if (timestamp < cutoff) break;

				// Check for stock changes (use STOCK_BASELINE)
				if (timestampSec >= STOCK_BASELINE) {
					const currentInStock = current.s !== false;
					const previousInStock = previous.s !== false;

					if (currentInStock && !previousInStock) {
						const key = `${itemId}-back_in_stock`;
						if (!seenItems.has(key)) {
							seenItems.add(key);
							feedItems.push({
								type: 'back_in_stock',
								item,
								timestamp,
								currentPrice: current.p,
								regularPrice: current.rp,
								history: sorted
							});
						}
						break;
					} else if (!currentInStock && previousInStock) {
						const key = `${itemId}-out_of_stock`;
						if (!seenItems.has(key)) {
							seenItems.add(key);
							feedItems.push({
								type: 'out_of_stock',
								item,
								timestamp,
								currentPrice: current.p,
								regularPrice: current.rp,
								history: sorted
							});
						}
						break;
					}
				}

				// Check for price changes (use TRACKING_BASELINE)
				if (timestampSec >= TRACKING_BASELINE) {
					if (current.p < previous.p) {
						const percentChange = ((current.p - previous.p) / previous.p) * 100;
						const key = `${itemId}-price_drop`;
						if (!seenItems.has(key)) {
							seenItems.add(key);
							feedItems.push({
								type: 'price_drop',
								item,
								timestamp,
								currentPrice: current.p,
								previousPrice: previous.p,
								percentChange,
								regularPrice: current.rp,
								previousRegularPrice: previous.rp,
								history: sorted
							});
						}
						break;
					} else if (current.p > previous.p) {
						const percentChange = ((current.p - previous.p) / previous.p) * 100;
						const key = `${itemId}-price_increase`;
						if (!seenItems.has(key)) {
							seenItems.add(key);
							feedItems.push({
								type: 'price_increase',
								item,
								timestamp,
								currentPrice: current.p,
								previousPrice: previous.p,
								percentChange,
								regularPrice: current.rp,
								previousRegularPrice: previous.rp,
								history: sorted
							});
						}
						break;
					}
				}
			}
		}

		// Sort by timestamp (most recent first)
		return feedItems.sort((a, b) => b.timestamp - a.timestamp);
	});

	// Filter feed by event type
	const filteredFeed = $derived(
		eventFilter === 'all' ? feed : feed.filter((item) => item.type === eventFilter)
	);

	// Count by type for badges
	const counts = $derived({
		all: feed.length,
		new: feed.filter((i) => i.type === 'new').length,
		price_drop: feed.filter((i) => i.type === 'price_drop').length,
		price_increase: feed.filter((i) => i.type === 'price_increase').length,
		back_in_stock: feed.filter((i) => i.type === 'back_in_stock').length,
		out_of_stock: feed.filter((i) => i.type === 'out_of_stock').length
	});

	// Pagination
	const PAGE_SIZE = 50;
	let visibleCount = $state(PAGE_SIZE);

	// Reset pagination when filters change
	$effect(() => {
		const _ = [timeFilter, eventFilter];
		visibleCount = PAGE_SIZE;
	});

	const visibleFeed = $derived(filteredFeed.slice(0, visibleCount));
	const hasMore = $derived(visibleCount < filteredFeed.length);

	// Format relative time
	function formatRelativeTime(timestamp: number): string {
		const now = Date.now();
		const diff = now - timestamp;
		const minutes = Math.floor(diff / (1000 * 60));
		const hours = Math.floor(minutes / 60);
		const days = Math.floor(hours / 24);

		if (days > 0) return `${days}d ago`;
		if (hours > 0) return `${hours}h ago`;
		if (minutes > 0) return `${minutes}m ago`;
		return 'Just now';
	}

	// Format full timestamp for tooltip
	function formatFullTimestamp(timestamp: number): string {
		return new Date(timestamp).toLocaleString('en-AU', {
			weekday: 'short',
			day: 'numeric',
			month: 'short',
			hour: 'numeric',
			minute: '2-digit',
			hour12: true
		});
	}

	// Format percentage change - show <1% for tiny changes
	function formatPercent(pct: number): string {
		const absPct = Math.abs(pct);
		if (absPct < 1 && absPct > 0) {
			return pct > 0 ? '<+1%' : '<-1%';
		}
		return `${pct > 0 ? '+' : ''}${pct.toFixed(0)}%`;
	}

	// Get event type styling
	function getEventStyle(type: FeedItem['type']) {
		switch (type) {
			case 'new':
				return {
					label: 'New',
					bg: 'bg-primary/20',
					text: 'text-primary',
					border: 'var(--primary)'
				};
			case 'price_drop':
				return {
					label: 'Price Drop',
					bg: 'bg-price-drop/20',
					text: 'text-price-drop',
					border: 'var(--price-drop)'
				};
			case 'price_increase':
				return {
					label: 'Price Up',
					bg: 'bg-price-rise/20',
					text: 'text-price-rise',
					border: 'var(--price-rise)'
				};
			case 'back_in_stock':
				return {
					label: 'Back in Stock',
					bg: 'bg-stock-available/20',
					text: 'text-stock-available',
					border: 'var(--stock-available)'
				};
			case 'out_of_stock':
				return {
					label: 'Out of Stock',
					bg: 'bg-stock-out/20',
					text: 'text-stock-out',
					border: 'var(--stock-out)'
				};
		}
	}

	// Infinite scroll
	function infiniteScroll(node: HTMLElement) {
		const observer = new IntersectionObserver(
			(entries) => {
				if (entries[0].isIntersecting && hasMore) {
					visibleCount = Math.min(visibleCount + PAGE_SIZE, filteredFeed.length);
				}
			},
			{ rootMargin: '200px' }
		);
		observer.observe(node);
		return { destroy: () => observer.disconnect() };
	}
</script>

<svelte:head>
	<title>Tracker - GSAU.gg</title>
	<meta
		name="description"
		content="Track price and stock changes on gel blaster products. See the latest price drops, restocks, and deals across Australian retailers."
	/>
	<link rel="canonical" href="https://www.gsau.gg/tracker" />
	<meta property="og:title" content="Tracker - GSAU.gg" />
	<meta
		property="og:description"
		content="Track price and stock changes on gel blaster products. See the latest price drops, restocks, and deals."
	/>
	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://www.gsau.gg/tracker" />
</svelte:head>

<div class="space-y-4">
	<!-- Compact header -->
	<div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
		<h1 class="text-xl sm:text-2xl font-bold tracking-tight">Tracker</h1>
		<p class="text-sm text-muted-foreground">
			<span class="font-mono font-semibold text-foreground tabular-nums">{feed.length}</span>
			changes
			<span class="text-border">•</span>
			<span class="font-mono font-semibold text-foreground tabular-nums"
				>{Object.values(itemHistory.data?.history ?? {})
					.filter((h) => h.length > 1)
					.length.toLocaleString()}</span
			> items tracked
		</p>
	</div>

	<!-- Filters row -->
	<div class="flex flex-wrap items-center gap-4">
		<!-- Time filter -->
		<div class="flex gap-1">
			{#each ['24h', '7d', '30d'] as filter}
				<button
					onclick={() => (timeFilter = filter as TimeFilter)}
					class="rounded-full px-3 py-1 text-sm font-medium transition-colors
						{timeFilter === filter
						? 'bg-primary text-primary-foreground'
						: 'bg-muted text-muted-foreground hover:bg-muted/80'}"
				>
					{filter}
				</button>
			{/each}
		</div>

		<Separator orientation="vertical" class="h-6" />

		<!-- Event type filter -->
		<div class="flex flex-wrap gap-1">
			<button
				onclick={() => (eventFilter = 'all')}
				class="rounded-full px-3 py-1 text-sm font-medium transition-colors
					{eventFilter === 'all'
					? 'bg-foreground text-background'
					: 'bg-muted text-muted-foreground hover:bg-muted/80'}"
			>
				All ({counts.all})
			</button>
			<button
				onclick={() => (eventFilter = 'new')}
				class="rounded-full px-3 py-1 text-sm font-medium transition-colors
					{eventFilter === 'new'
					? 'bg-primary text-primary-foreground'
					: 'bg-primary/20 text-primary hover:bg-primary/30'}
					{counts.new === 0 ? 'opacity-40' : ''}"
			>
				New ({counts.new})
			</button>
			<button
				onclick={() => (eventFilter = 'price_drop')}
				class="rounded-full px-3 py-1 text-sm font-medium transition-colors
					{eventFilter === 'price_drop'
					? 'bg-price-drop text-white'
					: 'bg-price-drop/20 text-price-drop hover:bg-price-drop/30'}
					{counts.price_drop === 0 ? 'opacity-40' : ''}"
			>
				Drops ({counts.price_drop})
			</button>
			<button
				onclick={() => (eventFilter = 'price_increase')}
				class="rounded-full px-3 py-1 text-sm font-medium transition-colors
					{eventFilter === 'price_increase'
					? 'bg-price-rise text-white'
					: 'bg-price-rise/20 text-price-rise hover:bg-price-rise/30'}
					{counts.price_increase === 0 ? 'opacity-40' : ''}"
			>
				Increases ({counts.price_increase})
			</button>
			<button
				onclick={() => (eventFilter = 'back_in_stock')}
				class="rounded-full px-3 py-1 text-sm font-medium transition-colors
					{eventFilter === 'back_in_stock'
					? 'bg-stock-available text-white'
					: 'bg-stock-available/20 text-stock-available hover:bg-stock-available/30'}
					{counts.back_in_stock === 0 ? 'opacity-40' : ''}"
			>
				In Stock ({counts.back_in_stock})
			</button>
			<button
				onclick={() => (eventFilter = 'out_of_stock')}
				class="rounded-full px-3 py-1 text-sm font-medium transition-colors
					{eventFilter === 'out_of_stock'
					? 'bg-stock-out text-white'
					: 'bg-stock-out/20 text-stock-out hover:bg-stock-out/30'}
					{counts.out_of_stock === 0 ? 'opacity-40' : ''}"
			>
				Out ({counts.out_of_stock})
			</button>
		</div>
	</div>

	{#if items.isLoading || itemHistory.isLoading}
		<div class="flex items-center gap-2 text-muted-foreground">
			<svg
				class="h-5 w-5 animate-spin"
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
			>
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
				></circle>
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				></path>
			</svg>
			<span>Loading feed...</span>
		</div>
	{:else if items.isError || itemHistory.isError}
		<Alert.Root variant="destructive" class="border-destructive/50 bg-destructive/10">
			<svg
				class="h-4 w-4"
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
				/>
			</svg>
			<Alert.Title>Error loading data</Alert.Title>
			<Alert.Description>Please try refreshing the page.</Alert.Description>
		</Alert.Root>
	{:else if filteredFeed.length === 0}
		<p class="py-8 text-center text-muted-foreground">
			No {eventFilter === 'all' ? 'changes' : eventFilter.replace('_', ' ')} in the selected time period.
		</p>
	{:else}
		<!-- Feed -->
		<div class="space-y-2">
			{#each visibleFeed as feedItem, i (feedItem.item.id + feedItem.type + feedItem.timestamp)}
				{@const style = getEventStyle(feedItem.type)}
				<article
					class="flex items-center gap-4 rounded-lg border border-border border-l-[5px] bg-card p-4 transition-all duration-200 hover:bg-muted/50 focus-visible:ring-border animate-in fade-in slide-in-from-left-2"
					style="border-left-color: {style.border}; animation-delay: {Math.min(i, 20) *
						30}ms; animation-fill-mode: backwards;"
				>
					<!-- Product image -->
					<div
						class="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-md bg-muted"
					>
						{#if feedItem.item.image}
							<img
								src={feedItem.item.image}
								alt=""
								class="h-full w-full object-contain"
								loading="lazy"
							/>
						{:else}
							<svg
								class="h-6 w-6 text-muted-foreground/50"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
								stroke-width="1.5"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"
								/>
							</svg>
						{/if}
					</div>

					<!-- Product info -->
					<div class="min-w-0 flex-1">
						<div class="flex items-center gap-2">
							<span class="rounded {style.bg} px-1.5 py-0.5 text-xs font-medium {style.text}">
								{style.label}
							</span>
							<Tooltip.Root>
								<Tooltip.Trigger class="cursor-default">
									<span class="text-xs tabular-nums text-muted-foreground"
										>{formatRelativeTime(feedItem.timestamp)}</span
									>
								</Tooltip.Trigger>
								<Tooltip.Content>
									{formatFullTimestamp(feedItem.timestamp)}
								</Tooltip.Content>
							</Tooltip.Root>
						</div>
						<a
							href="/?q={encodeURIComponent(feedItem.item.title)}"
							class="mt-1 block truncate text-sm font-medium hover:text-primary hover:underline"
						>
							{feedItem.item.title}
						</a>
						<div class="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-sm">
							{#if feedItem.type === 'price_drop' || feedItem.type === 'price_increase'}
								{#if feedItem.regularPrice && feedItem.regularPrice !== feedItem.currentPrice}
									<!-- On sale: show both regular and sale price changes -->
									<span class="text-muted-foreground">
										Regular: <span class="tabular-nums">{formatPrice(feedItem.regularPrice)}</span>
										{#if feedItem.previousRegularPrice && feedItem.previousRegularPrice !== feedItem.regularPrice}
											{@const rpChange =
												((feedItem.regularPrice - feedItem.previousRegularPrice) /
													feedItem.previousRegularPrice) *
												100}
											<span
												class="tabular-nums text-xs {rpChange > 0
													? 'text-price-rise'
													: 'text-price-drop'}"
											>
												({formatPercent(rpChange)})
											</span>
										{/if}
									</span>
									<span
										class="font-bold tabular-nums {feedItem.type === 'price_drop'
											? 'text-price-drop'
											: 'text-price-rise'}"
									>
										Sale: {formatPrice(feedItem.currentPrice)}
										<span class="font-normal tabular-nums text-xs">
											({formatPercent(feedItem.percentChange!)})
										</span>
									</span>
								{:else}
									<!-- Not on sale: just show price change -->
									<span class="tabular-nums text-muted-foreground line-through"
										>{formatPrice(feedItem.previousPrice!)}</span
									>
									<span
										class="font-bold tabular-nums {feedItem.type === 'price_drop'
											? 'text-price-drop'
											: 'text-price-rise'}"
									>
										{formatPrice(feedItem.currentPrice)}
									</span>
									<span
										class="tabular-nums text-xs {feedItem.type === 'price_drop'
											? 'text-price-drop'
											: 'text-price-rise'}"
									>
										({formatPercent(feedItem.percentChange!)})
									</span>
								{/if}
							{:else}
								<span class="font-bold tabular-nums">{formatPrice(feedItem.currentPrice)}</span>
							{/if}
							<a
								href={addUtmParams(feedItem.item.url)}
								target="_blank"
								rel="noopener noreferrer"
								onclick={() => trackStoreClick(feedItem.item.vendor)}
								class="text-xs text-muted-foreground hover:text-primary hover:underline"
							>
								• {feedItem.item.vendor}
							</a>
						</div>
					</div>

					<!-- Sparkline -->
					{#if feedItem.history.length >= 1}
						<div class="hidden shrink-0 sm:block">
							<PriceSparkline history={feedItem.history} width={100} height={40} />
						</div>
					{/if}
				</article>
			{/each}
		</div>

		<!-- Infinite scroll sentinel -->
		{#if hasMore}
			<div use:infiniteScroll class="h-4"></div>
		{/if}
	{/if}
</div>
