<script lang="ts">
	import { theme } from '$lib/stores/theme.svelte';
	import { browser } from '$app/environment';
	import { Button } from '$lib/components/ui/button';
	import Sun from '@lucide/svelte/icons/sun';
	import Moon from '@lucide/svelte/icons/moon';

	// Use theme.value directly with $derived
	const currentTheme = $derived(theme.value);

	const resolvedTheme = $derived.by(() => {
		if (!browser) return 'light';
		if (currentTheme === 'system') {
			return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		}
		return currentTheme;
	});

	const isDark = $derived(resolvedTheme === 'dark');
</script>

<Button
	variant="outline"
	size="icon"
	onclick={() => theme.toggle()}
	aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
>
	{#if isDark}
		<Moon class="size-[18px]" />
	{:else}
		<Sun class="size-[18px]" />
	{/if}
</Button>
