// Zod schemas for runtime validation of JSON data
import { z } from 'zod';

// Vendor schema
export const VendorSchema = z.object({
	name: z.string(),
	price: z.number(),
	regularPrice: z.number().nullable().optional(),
	url: z.string(),
	inStock: z.boolean(),
	sku: z.string().nullable().optional()
});

// Product schema
export const ProductSchema = z.object({
	id: z.string(),
	title: z.string(),
	image: z.string().nullable(),
	category: z.string(),
	tags: z.array(z.string()),
	vendors: z.array(VendorSchema),
	lowestPrice: z.number(),
	inStock: z.boolean()
});

// Products data schema
export const ProductsDataSchema = z.object({
	lastUpdated: z.string(),
	storeCount: z.number(),
	productCount: z.number(),
	products: z.array(ProductSchema)
});

// Price point schema
export const PricePointSchema = z.object({
	t: z.number(), // timestamp
	p: z.number(), // price
	rp: z.number().optional(), // regular price
	s: z.boolean().optional(), // stock status
	v: z.string().optional(), // vendor name
	prev: z.number().optional() // previous price
});

// Product price history schema
export const ProductPriceHistorySchema = z.object({
	vendors: z.record(z.string(), z.array(PricePointSchema)),
	lowest: z.array(PricePointSchema)
});

// Tracker data response schema
export const TrackerDataResponseSchema = z.object({
	lastUpdated: z.string(),
	history: z.record(z.string(), ProductPriceHistorySchema)
});

// Log entry schema
export const LogEntrySchema = z.object({
	time: z.string(),
	level: z.enum(['INFO', 'WARNING', 'ERROR', 'DEBUG']),
	message: z.string()
});

// Filtered product schema
export const FilteredProductSchema = z.object({
	title: z.string(),
	reason: z.string(),
	keyword: z.string(),
	filterCategory: z.string().optional()
});

// Store stats schema
export const StoreStatsSchema = z.object({
	name: z.string(),
	url: z.string(),
	platform: z.string(),
	fetched: z.number(),
	filtered: z.number(),
	final: z.number(),
	inStock: z.number(),
	outOfStock: z.number(),
	duration: z.number(),
	error: z.string().nullable(),
	cached_at: z.string().optional(),
	logs: z.array(LogEntrySchema),
	filteredProducts: z.array(FilteredProductSchema).optional()
});

// Stats schema
export const StatsSchema = z.object({
	lastUpdated: z.string(),
	duration: z.number(),
	stores: z.array(StoreStatsSchema)
});

// Item schema
export const ItemSchema = z.object({
	id: z.string(),
	storeId: z.string(),
	productId: z.string(),
	variantId: z.string(),
	title: z.string(),
	sku: z.string().nullable(),
	price: z.number(),
	regularPrice: z.number().nullable(),
	image: z.string().nullable(),
	url: z.string(),
	vendor: z.string(),
	category: z.string(),
	tags: z.array(z.string()),
	inStock: z.boolean()
});

// Items data schema
export const ItemsDataSchema = z.object({
	lastUpdated: z.string(),
	items: z.record(z.string(), ItemSchema)
});

// Item history data schema
export const ItemHistoryDataSchema = z.object({
	lastUpdated: z.string(),
	history: z.record(z.string(), z.array(PricePointSchema))
});

// Type exports (inferred from schemas)
export type VendorZ = z.infer<typeof VendorSchema>;
export type ProductZ = z.infer<typeof ProductSchema>;
export type ProductsDataZ = z.infer<typeof ProductsDataSchema>;
export type PricePointZ = z.infer<typeof PricePointSchema>;
export type ProductPriceHistoryZ = z.infer<typeof ProductPriceHistorySchema>;
export type TrackerDataResponseZ = z.infer<typeof TrackerDataResponseSchema>;
export type LogEntryZ = z.infer<typeof LogEntrySchema>;
export type StoreStatsZ = z.infer<typeof StoreStatsSchema>;
export type StatsZ = z.infer<typeof StatsSchema>;
export type ItemZ = z.infer<typeof ItemSchema>;
export type ItemsDataZ = z.infer<typeof ItemsDataSchema>;
export type ItemHistoryDataZ = z.infer<typeof ItemHistoryDataSchema>;
