<script lang="ts">
	import type { ProductPriceHistory } from '$lib/data/types';
	import { formatPrice } from '$lib/utils/format';
	import { onMount, onDestroy } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import * as Table from '$lib/components/ui/table';
	import type { Chart as ChartType } from 'chart.js';

	// Chart.js is lazy loaded to save ~200KB on initial page load
	let ChartJS: typeof ChartType | null = null;
	let chartLoading = $state(true);
	let chartError = $state<string | null>(null);

	interface Props {
		history: ProductPriceHistory;
		productTitle: string;
		width?: number;
		height?: number;
	}

	let { history, productTitle, width = 600, height = 300 }: Props = $props();

	let canvas: HTMLCanvasElement;
	let chart: ChartType | null = null;
	let showTable = $state(false);

	// Table data for accessibility
	const tableData = $derived.by(() => {
		const rows: Array<{
			date: string;
			timestamp: number;
			vendor: string;
			price: number;
			regularPrice?: number;
		}> = [];

		for (const [vendor, points] of Object.entries(history.vendors)) {
			for (const point of points) {
				const timestamp = point.t > 1e12 ? point.t : point.t * 1000;
				rows.push({
					date: new Date(timestamp).toLocaleString('en-AU', {
						day: 'numeric',
						month: 'short',
						hour: 'numeric',
						minute: '2-digit'
					}),
					timestamp,
					vendor,
					price: point.p,
					regularPrice: point.rp
				});
			}
		}

		return rows.sort((a, b) => b.timestamp - a.timestamp);
	});

	// Color palette for vendors
	const vendorColors = [
		'#14b8a6', // teal (primary)
		'#f59e0b', // amber
		'#8b5cf6', // violet
		'#ec4899', // pink
		'#10b981', // emerald
		'#f97316' // orange
	];

	// Build datasets from history
	function buildDatasets() {
		type PointContext = { dataIndex: number; dataset: { data: unknown[] } };
		const datasets: Array<{
			label: string;
			data: Array<{ x: number; y: number; rp?: number }>;
			borderColor: string;
			backgroundColor: string | ((ctx: PointContext) => string);
			borderDash?: number[];
			borderWidth: number;
			pointRadius: number | ((ctx: PointContext) => number);
			pointHoverRadius: number;
			pointBorderWidth?: number | ((ctx: PointContext) => number);
			stepped: 'after' | false;
			tension: number;
			isRegularPrice?: boolean;
		}> = [];

		const vendors = Object.keys(history.vendors);
		const now = Date.now();

		vendors.forEach((vendor, index) => {
			const vendorPoints = history.vendors[vendor];
			if (!vendorPoints || vendorPoints.length === 0) return;

			const color = vendorColors[index % vendorColors.length];

			// Sale price dataset
			const saleData = vendorPoints
				.map((p) => ({
					x: p.t > 1e12 ? p.t : p.t * 1000,
					y: p.p,
					rp: p.rp
				}))
				.sort((a, b) => a.x - b.x);

			// Add "now" point to extend line to current time (using last known price)
			const lastPoint = saleData[saleData.length - 1];
			if (lastPoint && lastPoint.x < now) {
				saleData.push({ x: now, y: lastPoint.y, rp: lastPoint.rp });
			}

			datasets.push({
				label: vendor,
				data: saleData,
				borderColor: color,
				// "Now" point is hollow (transparent fill), others are solid
				backgroundColor: (ctx) =>
					ctx.dataIndex === ctx.dataset.data.length - 1 ? 'transparent' : color,
				borderWidth: 2,
				// "Now" point slightly smaller with thicker border for ring effect
				pointRadius: (ctx) => (ctx.dataIndex === ctx.dataset.data.length - 1 ? 5 : 4),
				pointBorderWidth: (ctx) => (ctx.dataIndex === ctx.dataset.data.length - 1 ? 2 : 1),
				pointHoverRadius: 6,
				stepped: 'after',
				tension: 0
			});

			// Regular price dataset (if any points have rp)
			const regularData = vendorPoints
				.filter((p) => p.rp && p.rp > p.p)
				.map((p) => ({
					x: p.t > 1e12 ? p.t : p.t * 1000,
					y: p.rp!
				}))
				.sort((a, b) => a.x - b.x);

			if (regularData.length > 0) {
				// Add "now" point for regular price line too
				const lastRegular = regularData[regularData.length - 1];
				if (lastRegular && lastRegular.x < now) {
					regularData.push({ x: now, y: lastRegular.y });
				}

				datasets.push({
					label: `${vendor} (Regular)`,
					data: regularData,
					borderColor: color,
					backgroundColor: 'transparent',
					borderDash: [5, 5],
					borderWidth: 1.5,
					// "Now" point as hollow ring, others as small dots
					pointRadius: (ctx) => (ctx.dataIndex === ctx.dataset.data.length - 1 ? 4 : 2),
					pointBorderWidth: (ctx) => (ctx.dataIndex === ctx.dataset.data.length - 1 ? 2 : 1),
					pointHoverRadius: 4,
					stepped: 'after',
					tension: 0,
					isRegularPrice: true
				});
			}
		});

		return datasets;
	}

	// Get computed colors from CSS variables
	function getThemeColors() {
		if (typeof document === 'undefined') {
			return {
				foreground: '#0f172a',
				mutedForeground: '#64748b',
				border: '#e2e8f0',
				popover: '#ffffff',
				popoverForeground: '#0f172a'
			};
		}
		const style = getComputedStyle(document.documentElement);
		const isDark = document.documentElement.classList.contains('dark');
		return {
			foreground: isDark ? '#f1f5f9' : '#0f172a',
			mutedForeground: isDark ? '#94a3b8' : '#64748b',
			border: isDark ? '#334155' : '#e2e8f0',
			popover: isDark ? '#1e293b' : '#ffffff',
			popoverForeground: isDark ? '#f1f5f9' : '#0f172a'
		};
	}

	function createChart() {
		if (!canvas || !ChartJS) return;

		const datasets = buildDatasets();
		const colors = getThemeColors();

		// Calculate min/max for y-axis with padding and nice round numbers
		const allPrices = datasets.flatMap((d) => d.data.map((p) => p.y));
		const minPrice = Math.min(...allPrices);
		const maxPrice = Math.max(...allPrices);
		const range = maxPrice - minPrice || 10;

		// Round to nice intervals
		const step = Math.pow(10, Math.floor(Math.log10(range))) / 2;
		const niceMin = Math.floor(minPrice / step) * step - step;
		const niceMax = Math.ceil(maxPrice / step) * step + step;

		chart = new ChartJS(canvas, {
			type: 'line',
			data: { datasets },
			options: {
				responsive: true,
				maintainAspectRatio: false,
				interaction: {
					mode: 'index',
					intersect: false
				},
				scales: {
					x: {
						type: 'time',
						time: {
							unit: 'day',
							displayFormats: {
								day: 'd MMM'
							},
							tooltipFormat: 'EEE, d MMM'
						},
						grid: {
							display: false
						},
						ticks: {
							maxTicksLimit: 6,
							color: colors.mutedForeground
						}
					},
					y: {
						min: niceMin,
						max: niceMax,
						grid: {
							color: colors.border + '80'
						},
						ticks: {
							callback: (value) => formatPrice(value as number),
							color: colors.mutedForeground
						}
					}
				},
				plugins: {
					legend: {
						display: true,
						position: 'bottom',
						labels: {
							usePointStyle: true,
							pointStyle: 'circle',
							padding: 16,
							color: colors.foreground
						}
					},
					tooltip: {
						backgroundColor: colors.popover,
						titleColor: colors.popoverForeground,
						bodyColor: colors.popoverForeground,
						borderColor: colors.border,
						borderWidth: 1,
						padding: 12,
						displayColors: true,
						filter: (item) => {
							// Hide regular price lines from tooltip (they clutter it)
							return !item.dataset.label?.includes('(Regular)');
						},
						callbacks: {
							label: (context) => {
								const dataset = context.dataset as (typeof datasets)[0];
								const dataPoint = context.raw as { x: number; y: number; rp?: number };
								const price = formatPrice(dataPoint.y);

								if (dataPoint.rp && dataPoint.rp > dataPoint.y) {
									const discount = Math.round(((dataPoint.rp - dataPoint.y) / dataPoint.rp) * 100);
									return `${dataset.label}: ${price} (was ${formatPrice(dataPoint.rp)}, ${discount}% off)`;
								}

								return `${dataset.label}: ${price}`;
							}
						}
					}
				}
			}
		});
	}

	function updateChart() {
		if (!chart) return;

		const datasets = buildDatasets();
		chart.data.datasets = datasets;

		// Recalculate y-axis with nice numbers
		const allPrices = datasets.flatMap((d) => d.data.map((p) => p.y));
		const minPrice = Math.min(...allPrices);
		const maxPrice = Math.max(...allPrices);
		const range = maxPrice - minPrice || 10;
		const step = Math.pow(10, Math.floor(Math.log10(range))) / 2;
		const niceMin = Math.floor(minPrice / step) * step - step;
		const niceMax = Math.ceil(maxPrice / step) * step + step;

		if (chart.options.scales?.y) {
			chart.options.scales.y.min = niceMin;
			chart.options.scales.y.max = niceMax;
		}

		chart.update();
	}

	// Track whether component is mounted to prevent updates after destroy
	let isMounted = false;

	// Lazy load Chart.js
	async function loadChartJS() {
		try {
			// Import Chart.js and its date adapter (adapter is imported for side effects only)
			const chartModule = await import('chart.js');
			// @ts-ignore - chartjs-adapter-date-fns has no types
			await import('chartjs-adapter-date-fns');

			const {
				Chart,
				LineController,
				LineElement,
				PointElement,
				LinearScale,
				TimeScale,
				Tooltip,
				Legend,
				Filler
			} = chartModule;

			// Register components
			Chart.register(
				LineController,
				LineElement,
				PointElement,
				LinearScale,
				TimeScale,
				Tooltip,
				Legend,
				Filler
			);

			ChartJS = Chart;
			return true;
		} catch (err) {
			console.error('Failed to load Chart.js:', err);
			chartError = 'Failed to load chart library';
			return false;
		}
	}

	onMount(async () => {
		isMounted = true;
		chartLoading = true;

		const loaded = await loadChartJS();

		// Check if component was unmounted while loading
		if (!isMounted) return;

		chartLoading = false;

		if (loaded) {
			createChart();
		}
	});

	onDestroy(() => {
		isMounted = false;
		if (chart) {
			chart.destroy();
			chart = null;
		}
	});

	// Update chart when history changes (with cleanup)
	$effect(() => {
		history; // Track dependency
		if (isMounted && chart && ChartJS) {
			updateChart();
		}
		// Cleanup function runs when effect re-runs or component unmounts
		return () => {
			// No-op cleanup - actual cleanup is in onDestroy
		};
	});
</script>

<div class="space-y-2">
	<div style="height: {height}px;" class="relative">
		{#if chartLoading}
			<div class="absolute inset-0 flex items-center justify-center bg-muted/50 rounded-lg">
				<div class="flex flex-col items-center gap-2 text-muted-foreground">
					<svg
						class="animate-spin h-6 w-6"
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
					<span class="text-sm">Loading chart...</span>
				</div>
			</div>
		{:else if chartError}
			<div class="absolute inset-0 flex items-center justify-center bg-muted/50 rounded-lg">
				<p class="text-sm text-destructive">{chartError}</p>
			</div>
		{/if}
		<canvas
			bind:this={canvas}
			aria-label="Price history chart for {productTitle}"
			class:opacity-0={chartLoading || chartError}
		></canvas>
	</div>

	<!-- Legend note for regular price -->
	<p class="text-xs text-muted-foreground text-center">
		Dashed lines show regular price when item is on sale
	</p>

	<!-- Toggle table button -->
	<div class="flex justify-end">
		<Button variant="link" size="sm" onclick={() => (showTable = !showTable)}>
			{showTable ? 'Hide table' : 'Show as table'}
		</Button>
	</div>

	<!-- Accessible data table -->
	{#if showTable}
		<div class="max-h-64 overflow-auto rounded-lg border scrollbar-none">
			<Table.Root>
				<Table.Header>
					<Table.Row>
						<Table.Head>Date</Table.Head>
						<Table.Head>Vendor</Table.Head>
						<Table.Head class="text-right">Sale</Table.Head>
						<Table.Head class="text-right">Regular</Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each tableData as row}
						{@const isOnSale = row.regularPrice && row.regularPrice > row.price}
						<Table.Row>
							<Table.Cell class="text-muted-foreground">{row.date}</Table.Cell>
							<Table.Cell>{row.vendor}</Table.Cell>
							<Table.Cell
								class="text-right tabular-nums {isOnSale
									? 'font-medium text-price-drop'
									: 'text-muted-foreground'}"
							>
								{isOnSale ? formatPrice(row.price) : '-'}
							</Table.Cell>
							<Table.Cell class="text-right font-medium tabular-nums">
								{formatPrice(row.regularPrice ?? row.price)}
							</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
		</div>
	{/if}
</div>
