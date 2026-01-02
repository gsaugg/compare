<script lang="ts">
	import type { PricePoint } from '$lib/data/types';
	import { Sparkline } from 'sparkline-svelte';

	interface Props {
		history: PricePoint[];
		width?: number;
		height?: number;
	}

	let { history, width = 80, height = 32 }: Props = $props();

	// Need at least 1 point to show anything
	const hasEnoughData = $derived(history.length >= 1);

	// Prepare data for sparkline-svelte
	// We need to interpolate points based on time to properly show the x-axis scale
	const data = $derived.by(() => {
		if (!hasEnoughData) return [];

		// Sort by timestamp (oldest first)
		const sorted = [...history].sort((a, b) => a.t - b.t);

		// Get time range (30 days in seconds)
		const now = Math.floor(Date.now() / 1000);
		const thirtyDaysAgo = now - 30 * 24 * 60 * 60;
		const timeRange = now - thirtyDaysAgo;

		// Create 30 data points (one per day) interpolating between known prices
		const points: number[] = [];
		for (let i = 0; i < 30; i++) {
			const targetTime = thirtyDaysAgo + (i / 29) * timeRange;

			// Find the price at this time (last known price before or at this time)
			let price = sorted[0].p; // Default to first known price
			for (const point of sorted) {
				if (point.t <= targetTime) {
					price = point.p;
				} else {
					break;
				}
			}
			points.push(price);
		}

		return points;
	});

	// Calculate trend for color
	const trend = $derived.by(() => {
		if (!hasEnoughData) return 'flat';
		const sorted = [...history].sort((a, b) => a.t - b.t);
		const firstPrice = sorted[0].p;
		const lastPrice = sorted[sorted.length - 1].p;
		const percentChange = ((lastPrice - firstPrice) / firstPrice) * 100;

		if (percentChange < -1) return 'down';
		if (percentChange > 1) return 'up';
		return 'flat';
	});

	// Color based on trend (CSS custom properties)
	const lineColor = $derived(
		trend === 'down'
			? 'hsl(142, 76%, 36%)'
			: trend === 'up'
				? 'hsl(38, 92%, 50%)'
				: 'hsl(220, 9%, 46%)'
	);

	// Aria label for accessibility
	const ariaLabel = $derived(
		`Price trend: ${trend === 'down' ? 'decreasing' : trend === 'up' ? 'increasing' : 'stable'}`
	);
</script>

{#if hasEnoughData}
	<div
		class="shrink-0"
		style="width: {width}px; height: {height}px;"
		role="img"
		aria-label={ariaLabel}
	>
		<Sparkline
			{data}
			options={{
				lineColor,
				fillColor: 'transparent',
				strokeWidth: 2,
				spotRadius: 3,
				interactive: false,
				svgClass: 'w-full h-full'
			}}
		/>
	</div>
{:else}
	<!-- Not enough data placeholder -->
	<div class="flex items-center justify-center" style="width: {width}px; height: {height}px;">
		<span class="text-[10px] text-muted-foreground">--</span>
	</div>
{/if}
