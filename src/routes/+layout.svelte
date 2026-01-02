<script lang="ts">
	import '../app.css';
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import Header from '$lib/components/layout/Header.svelte';
	import MobileNav from '$lib/components/layout/MobileNav.svelte';
	import * as Tooltip from '$lib/components/ui/tooltip';

	let { children } = $props();

	// Create a single QueryClient instance
	const queryClient = new QueryClient({
		defaultOptions: {
			queries: {
				staleTime: 1000 * 60 * 60, // 1 hour default
				refetchOnWindowFocus: true
			}
		}
	});
</script>

<QueryClientProvider client={queryClient}>
	<Tooltip.Provider>
		<div class="min-h-screen bg-background text-foreground">
			<!-- Skip to main content link (accessibility) -->
			<a
				href="#main-content"
				class="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:outline-none"
			>
				Skip to main content
			</a>
			<Header />
			<main id="main-content" class="container mx-auto px-4 py-6 pb-20 lg:pb-6" tabindex="-1">
				{@render children()}
			</main>
			<MobileNav />
		</div>
	</Tooltip.Provider>
</QueryClientProvider>
