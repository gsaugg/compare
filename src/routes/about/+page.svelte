<script lang="ts">
	// About page - static content, no data fetching needed
</script>

<svelte:head>
	<title>About - GSAU.gg</title>
	<meta
		name="description"
		content="Learn about GSAU.gg, the Australian gel blaster price comparison tool built by the Gelsoft AU Discord community."
	/>
	<link rel="canonical" href="https://www.gsau.gg/about" />
	<meta property="og:title" content="About - GSAU.gg" />
	<meta
		property="og:description"
		content="Learn about GSAU.gg, the Australian gel blaster price comparison tool built by the Gelsoft AU Discord community."
	/>
	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://www.gsau.gg/about" />
</svelte:head>

<article class="prose prose-slate dark:prose-invert mx-auto max-w-3xl">
	<h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">About This Project</h1>

	<p class="text-lg text-muted-foreground">
		<strong class="text-foreground">GSAU.gg</strong> is an official Gelsoft AU Discord community project
		that helps Australian gel blaster enthusiasts find the best prices across multiple online retailers.
	</p>

	<section class="mt-6 sm:mt-8">
		<h2 class="text-xl font-semibold text-foreground">What We Do</h2>
		<p class="text-muted-foreground">
			We automatically collect publicly available product and pricing information from Australian
			gel blaster retailers and present it in an easy-to-compare format. This helps you make
			informed purchasing decisions without having to manually check multiple websites.
		</p>
	</section>

	<section class="mt-6 sm:mt-8">
		<h2 class="text-xl font-semibold text-foreground">How It Works</h2>
		<p class="text-muted-foreground">
			This is a static site hosted on GitHub Pages - there's no backend server. All the product data
			is pre-generated and loaded into your browser, where all filtering, searching, and sorting
			happens locally. This means the site works fast once loaded, but it does need to download the
			full product list upfront.
		</p>
		<p class="mt-3 text-muted-foreground">
			Our scraper is configured to run hourly via GitHub Actions, though exact timing may vary
			depending on GitHub's scheduling. All product information is sourced from publicly accessible
			APIs provided by the retailers themselves (Shopify, WooCommerce, and Squarespace stores). We
			do not have any special access or partnerships with these stores.
		</p>
		<p class="mt-3 text-muted-foreground">The raw data is processed through several stages:</p>
		<ul class="mt-3 space-y-2 text-muted-foreground">
			<li>
				<strong class="text-foreground">Filtering:</strong> We exclude non-gel-blaster products like trading
				cards, RC parts, model kits, collectibles, and clothing using keyword matching on titles, tags,
				and categories.
			</li>
			<li>
				<strong class="text-foreground">Normalisation:</strong> Product titles are cleaned up (removing
				SEO spam), and categories are standardised across different store naming conventions.
			</li>
			<li>
				<strong class="text-foreground">Grouping:</strong> Products from different stores are matched
				together using SKU codes where available, or fuzzy title matching (90% similarity threshold) as
				a fallback. This lets you compare the same product across multiple retailers.
			</li>
			<li>
				<strong class="text-foreground">Price Tracking:</strong> We record price changes over a 1-year
				rolling window, tracking both sale prices and regular prices to help identify genuine discounts.
			</li>
		</ul>
		<p class="mt-3 text-muted-foreground">
			While we don't intentionally modify the pricing data we receive, we do perform calculations on
			it - such as determining the lowest price, calculating discount percentages, and identifying
			price changes over time.
		</p>
	</section>

	<section class="mt-6 sm:mt-8">
		<h2 class="text-xl font-semibold text-foreground">Features</h2>
		<p class="text-muted-foreground">
			Beyond the main product comparison, you can use the
			<a href="/tracker" class="text-primary hover:underline">Tracker page</a> to see price drops
			and new products from the last 24 hours, the
			<a href="/map" class="text-primary hover:underline">Map page</a> to find stores and fields
			near you, and the
			<a href="/status" class="text-primary hover:underline">Status page</a> to see detailed scraper logs
			and store health.
		</p>
		<h3 class="mt-4 text-lg font-medium text-foreground">Map</h3>
		<p class="text-muted-foreground">
			The <a href="/map" class="text-primary hover:underline">Map page</a> shows gel blaster stores and
			fields across Australia. You can filter by type (store or field) and state, click on markers to
			see details and get directions via Google Maps, and use the "Locate me" button to find locations
			near you sorted by distance. Some locations are both a store and a field.
		</p>
		<h3 class="mt-4 text-lg font-medium text-foreground">Search</h3>
		<p class="text-muted-foreground">
			Search uses a two-stage approach. First, it tries word-based matching where all your search
			terms must appear somewhere in the product's title, category, SKU codes, or tags. For example,
			searching "glock green" will only show products containing both words. Hyphens are treated as
			spaces, so "KS-1", "KS 1", and "KS1" will all match each other.
		</p>
		<p class="mt-2 text-muted-foreground">
			If word-based search finds nothing, we fall back to fuzzy matching using
			<a
				href="https://www.fusejs.io/"
				target="_blank"
				rel="noopener"
				class="text-primary hover:underline">Fuse.js</a
			>
			with a 0.3 threshold (where 0 is exact match and 1 matches anything). This helps catch typos and
			close variations. Search results are cached to speed up repeated searches.
		</p>
	</section>

	<section class="mt-6 sm:mt-8">
		<h2 class="text-xl font-semibold text-foreground">Transparency</h2>
		<p class="text-muted-foreground">
			You can see exactly what's happening behind the scenes on the
			<a href="/status" class="text-primary hover:underline">Status page</a>. This shows you the
			full list of stores we scrape from, when each store was last updated, and detailed logs
			including which products were filtered out and why. This project is open source under the
			<a
				href="https://www.gnu.org/licenses/agpl-3.0.html"
				target="_blank"
				rel="noopener"
				class="text-primary hover:underline">AGPL-3.0 license</a
			>
			and all source code is
			<a
				href="https://github.com/gsaugg/compare"
				target="_blank"
				rel="noopener"
				class="text-primary hover:underline">available on GitHub</a
			> for review. Contributions are welcome.
		</p>
		<p class="mt-3 text-muted-foreground">
			This site does not use affiliate links and we don't make any money from it. When you click
			through to a store, we add UTM parameters to the URL so we can see which stores are getting
			traffic in Google Analytics - but these are not affiliate tracking links and we receive no
			commission.
		</p>
		<p class="mt-3 text-muted-foreground">
			The site is fully responsive and works on mobile devices. AI-assisted coding tools have been
			used in the development of this project.
		</p>
	</section>

	<section class="mt-6 sm:mt-8">
		<h2 class="text-xl font-semibold text-foreground">Fair to Stores</h2>
		<p class="text-muted-foreground">
			We aim to treat all retailers fairly. When multiple stores have the same price for a product,
			we randomise the order they appear in. This means no single store gets preferential placement
			just because of alphabetical ordering or when they were added to our system.
		</p>
	</section>

	<section class="mt-6 sm:mt-8">
		<h2 class="text-xl font-semibold text-foreground">For Store Owners</h2>
		<p class="text-muted-foreground">
			Stores are welcome to use this site just as much as enthusiasts - whether for market research,
			competitor analysis, or anything else. If your store is listed and you would like to be
			removed, please
			<a href="mailto:hello@gsau.gg" class="text-primary hover:underline">get in contact</a> and we will
			remove you. If you run an Australian gel blaster store and would like to be added, we'd love to
			hear from you. We reserve the right to choose which stores appear on this site, but will generally
			accept all Australian retailers.
		</p>
	</section>

	<section class="mt-6 sm:mt-8">
		<h2 class="text-xl font-semibold text-foreground">We May Get It Wrong</h2>
		<p class="text-muted-foreground">
			This is an automated system and it's not perfect. Our matching algorithm might incorrectly
			group different products together, or fail to recognise that two listings are the same item.
			Categories may be wrong, and some gel blaster products might get filtered out while
			non-gel-blaster items slip through. If you spot an error, please let us know on
			<a
				href="https://discord.gg/rmfZtWD95f"
				target="_blank"
				rel="noopener"
				class="text-primary hover:underline">Discord</a
			>,
			<a
				href="https://github.com/gsaugg/compare/issues"
				target="_blank"
				rel="noopener"
				class="text-primary hover:underline">GitHub</a
			>, or email us at
			<a href="mailto:hello@gsau.gg" class="text-primary hover:underline">hello@gsau.gg</a>.
		</p>
	</section>

	<section class="mt-6 sm:mt-8">
		<h2 class="text-xl font-semibold text-foreground">Disclaimer</h2>
		<ul class="space-y-3 text-muted-foreground">
			<li>
				<strong class="text-foreground">Accuracy:</strong> While we strive to keep information up-to-date,
				prices and availability can change at any time. Always verify details on the retailer's website
				before making a purchase.
			</li>
			<li>
				<strong class="text-foreground">Affiliation:</strong> This site is not affiliated with, endorsed
				by, or officially connected to any of the retailers listed.
			</li>
			<li>
				<strong class="text-foreground">Copyright:</strong> All product names, images, descriptions, and
				trademarks are the property of their respective owners. We use this information under fair use
				for price comparison purposes.
			</li>
			<li>
				<strong class="text-foreground">No Warranty:</strong> This service is provided "as is" without
				any warranties. We are not responsible for any purchasing decisions made based on information
				displayed here.
			</li>
		</ul>
	</section>

	<section class="mt-6 sm:mt-8">
		<h2 class="text-xl font-semibold text-foreground">Privacy</h2>
		<p class="text-muted-foreground">
			We use Google Analytics to see which pages are viewed and which stores get clicked. This data
			is sent to Google and we can't control what they do with it. We don't require accounts or
			collect any personal information ourselves. If you'd prefer not to be tracked, any ad blocker
			(like uBlock Origin) will block Google Analytics automatically. Your theme preference is
			stored locally in your browser and never sent anywhere.
		</p>
	</section>

	<section class="mt-6 sm:mt-8">
		<h2 class="text-xl font-semibold text-foreground">Community & Contact</h2>
		<p class="text-muted-foreground">
			This project is maintained by the <strong class="text-foreground">Gelsoft AU Discord</strong>
			community. For questions, suggestions, or to report issues, reach out via
			<a
				href="https://discord.gg/rmfZtWD95f"
				target="_blank"
				rel="noopener"
				class="text-primary hover:underline">Discord</a
			>,
			<a
				href="https://github.com/gsaugg/compare/issues"
				target="_blank"
				rel="noopener"
				class="text-primary hover:underline">GitHub</a
			>, or
			<a href="mailto:hello@gsau.gg" class="text-primary hover:underline">hello@gsau.gg</a>.
		</p>
		<p class="mt-3 text-muted-foreground">
			<strong class="text-foreground">Note:</strong> The Gelsoft AU Discord community has no relation
			or affiliation to the "Gelsoft Australia" field operated by Tactical Edge Hobbies.
		</p>
		<a
			href="https://discord.gg/rmfZtWD95f"
			target="_blank"
			rel="noopener"
			class="mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 sm:inline-flex sm:w-auto"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="currentColor"
			>
				<path
					d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"
				/>
			</svg>
			Join Gelsoft AU Discord
		</a>
	</section>

	<hr class="mt-6 sm:mt-8 border-border" />
	<p class="mt-3 sm:mt-4 text-sm text-muted-foreground">
		We try to keep this page up to date with how things work, but we may have missed something. If
		you have questions about anything not covered here, please get in touch.
	</p>
</article>
