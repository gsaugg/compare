<script lang="ts">
	interface Props {
		title: string;
		description: string;
		url: string;
		image?: string;
		imageAlt?: string;
		type?: 'website' | 'article';
		noindex?: boolean;
	}

	const SITE_NAME = 'GSAU.gg';
	const DEFAULT_IMAGE = 'https://www.gsau.gg/og-default.png';

	let {
		title,
		description,
		url,
		image,
		imageAlt,
		type = 'website',
		noindex = false
	}: Props = $props();

	const ogImage = $derived(image || DEFAULT_IMAGE);
</script>

<svelte:head>
	<title>{title}</title>
	<meta name="description" content={description} />
	<link rel="canonical" href={url} />

	{#if noindex}
		<meta name="robots" content="noindex, nofollow" />
	{/if}

	<!-- Open Graph -->
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta property="og:type" content={type} />
	<meta property="og:url" content={url} />
	<meta property="og:image" content={ogImage} />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	{#if imageAlt}
		<meta property="og:image:alt" content={imageAlt} />
	{/if}
	<meta property="og:site_name" content={SITE_NAME} />
	<meta property="og:locale" content="en_AU" />

	<!-- Twitter Card -->
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={title} />
	<meta name="twitter:description" content={description} />
	<meta name="twitter:image" content={ogImage} />
</svelte:head>
