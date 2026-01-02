// Formatting utilities

export function formatPrice(price: number): string {
	// Round to cents to avoid floating point issues (e.g., 15.990000000001)
	const rounded = Math.round(price * 100) / 100;
	// Show cents if the price has them, otherwise hide unnecessary decimals
	const hasCents = Math.abs(rounded - Math.round(rounded)) > 0.001;
	return new Intl.NumberFormat('en-AU', {
		style: 'currency',
		currency: 'AUD',
		minimumFractionDigits: hasCents ? 2 : 0,
		maximumFractionDigits: 2
	}).format(rounded);
}

export function formatPriceWithCents(price: number): string {
	return new Intl.NumberFormat('en-AU', {
		style: 'currency',
		currency: 'AUD',
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	}).format(price);
}

export function getDiscountPercent(price: number, regularPrice?: number | null): number {
	if (!regularPrice) return 0;
	// Round to cents to avoid floating point issues
	const roundedPrice = Math.round(price * 100) / 100;
	const roundedRegular = Math.round(regularPrice * 100) / 100;
	// Use small epsilon for comparison
	if (roundedPrice >= roundedRegular - 0.01) return 0;
	return Math.round(((roundedRegular - roundedPrice) / roundedRegular) * 100);
}

export function truncateTitle(title: string, maxLength: number = 60): string {
	if (title.length <= maxLength) return title;
	return title.slice(0, maxLength).trim() + '...';
}

/**
 * Compare two prices with tolerance for floating point errors
 * Returns: -1 if a < b, 0 if a == b, 1 if a > b
 */
export function comparePrices(a: number, b: number): number {
	const roundedA = Math.round(a * 100);
	const roundedB = Math.round(b * 100);
	if (roundedA < roundedB) return -1;
	if (roundedA > roundedB) return 1;
	return 0;
}

/**
 * Check if two prices are equal (within floating point tolerance)
 */
export function pricesEqual(a: number, b: number): boolean {
	return Math.round(a * 100) === Math.round(b * 100);
}

/**
 * Add UTM referral parameters to a store URL
 */
export function addUtmParams(url: string): string {
	try {
		const parsed = new URL(url);
		parsed.searchParams.set('utm_source', 'gsau.gg');
		parsed.searchParams.set('utm_medium', 'referral');
		return parsed.toString();
	} catch {
		return url;
	}
}

/**
 * Track store click event in GA4
 */
export function trackStoreClick(storeName: string): void {
	if (typeof window !== 'undefined' && typeof window.gtag === 'function') {
		window.gtag('event', 'store_click', {
			store_name: storeName
		});
	}
}
