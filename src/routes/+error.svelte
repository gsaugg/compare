<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button';
	import * as Alert from '$lib/components/ui/alert';

	const statusCode = $derived($page.status);
	const errorMessage = $derived($page.error?.message ?? 'An unexpected error occurred');

	const isNotFound = $derived(statusCode === 404);
	const title = $derived(isNotFound ? 'Page Not Found' : 'Something Went Wrong');
	const description = $derived(
		isNotFound ? "The page you're looking for doesn't exist or has been moved." : errorMessage
	);

	function handleReload() {
		window.location.reload();
	}
</script>

<svelte:head>
	<title>{title} - GSAU.gg</title>
</svelte:head>

<div class="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
	<div class="max-w-md space-y-6">
		<!-- Error code -->
		<div class="text-8xl font-bold text-muted-foreground/30">{statusCode}</div>

		<!-- Error message -->
		<div class="space-y-2">
			<h1 class="text-2xl font-bold tracking-tight">{title}</h1>
			<p class="text-muted-foreground">{description}</p>
		</div>

		<!-- Alert for non-404 errors -->
		{#if !isNotFound}
			<Alert.Root variant="destructive" class="text-left">
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
				<Alert.Title>Error Details</Alert.Title>
				<Alert.Description class="font-mono text-xs">{errorMessage}</Alert.Description>
			</Alert.Root>
		{/if}

		<!-- Action buttons -->
		<div class="flex flex-col gap-2 sm:flex-row sm:justify-center">
			<Button href="/" variant="default">Go Home</Button>
			{#if !isNotFound}
				<Button variant="outline" onclick={handleReload}>Try Again</Button>
			{/if}
		</div>
	</div>
</div>
