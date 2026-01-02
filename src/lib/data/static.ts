// Static JSON data provider - fetches from /data/*.json
import type {
	DataProvider,
	ProductsData,
	TrackerDataResponse,
	ItemsData,
	ItemHistoryData,
	Stats
} from './types';
import {
	ProductsDataSchema,
	TrackerDataResponseSchema,
	ItemsDataSchema,
	ItemHistoryDataSchema,
	StatsSchema
} from './schemas';
import { ZodError } from 'zod';

// Retry configuration
const MAX_RETRIES = 3;
const INITIAL_DELAY_MS = 1000;
const REQUEST_TIMEOUT_MS = 10000;

/**
 * Delay execution for a given number of milliseconds
 */
function delay(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Fetch with timeout and abort controller
 */
async function fetchWithTimeout(url: string, timeout = REQUEST_TIMEOUT_MS): Promise<Response> {
	const controller = new AbortController();
	const id = setTimeout(() => controller.abort(), timeout);

	try {
		const response = await fetch(url, { signal: controller.signal });
		return response;
	} finally {
		clearTimeout(id);
	}
}

/**
 * Fetch with retry logic and exponential backoff
 */
async function fetchWithRetry<T>(url: string, validate: (data: unknown) => T): Promise<T> {
	let lastError: Error | null = null;

	for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
		try {
			const response = await fetchWithTimeout(url);

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const data = await response.json();

			// Validate data with Zod schema
			try {
				return validate(data);
			} catch (validationError) {
				if (validationError instanceof ZodError) {
					console.error(`Validation error for ${url}:`, validationError.issues);
					// Don't retry validation errors - the data is invalid
					throw new Error(`Invalid data format: ${validationError.issues[0]?.message}`);
				}
				throw validationError;
			}
		} catch (error) {
			lastError = error instanceof Error ? error : new Error(String(error));

			// Don't retry validation errors
			if (lastError.message.startsWith('Invalid data format:')) {
				throw lastError;
			}

			// Don't retry on the last attempt
			if (attempt < MAX_RETRIES - 1) {
				const delayMs = INITIAL_DELAY_MS * Math.pow(2, attempt);
				console.warn(`Fetch failed for ${url}, retrying in ${delayMs}ms...`, lastError.message);
				await delay(delayMs);
			}
		}
	}

	throw lastError ?? new Error(`Failed to fetch ${url} after ${MAX_RETRIES} attempts`);
}

export const dataProvider: DataProvider = {
	async getProducts(): Promise<ProductsData> {
		return fetchWithRetry('/data/products.json', (data) => ProductsDataSchema.parse(data));
	},

	async getTrackerData(): Promise<TrackerDataResponse> {
		return fetchWithRetry('/data/tracker-data.json', (data) =>
			TrackerDataResponseSchema.parse(data)
		);
	},

	async getItems(): Promise<ItemsData> {
		return fetchWithRetry('/data/items.json', (data) => ItemsDataSchema.parse(data));
	},

	async getItemHistory(): Promise<ItemHistoryData> {
		return fetchWithRetry('/data/item-history.json', (data) => ItemHistoryDataSchema.parse(data));
	},

	async getStats(): Promise<Stats> {
		return fetchWithRetry('/data/stats.json', (data) => StatsSchema.parse(data));
	}
};
