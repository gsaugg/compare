// Product and vendor types based on products.json structure

export interface Vendor {
	name: string;
	price: number;
	regularPrice?: number | null;
	url: string;
	inStock: boolean;
	sku?: string | null;
}

export interface Product {
	id: string;
	title: string;
	image: string | null;
	category: string;
	tags: string[];
	vendors: Vendor[];
	lowestPrice: number;
	inStock: boolean;
}

export interface ProductsData {
	lastUpdated: string;
	storeCount: number;
	productCount: number;
	products: Product[];
}

// Tracker data types
export interface PricePoint {
	t: number; // timestamp
	p: number; // price
	rp?: number; // regular price (when on sale)
	s?: boolean; // stock status (false = out of stock)
	v?: string; // vendor name (for lowest price entries)
	prev?: number; // previous price (for price drops)
}

export interface ProductPriceHistory {
	vendors: {
		[vendorName: string]: PricePoint[];
	};
	lowest: PricePoint[];
}

export interface TrackerDataResponse {
	lastUpdated: string;
	history: {
		[productId: string]: ProductPriceHistory;
	};
}

// Stats data types
export interface LogEntry {
	time: string;
	level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
	message: string;
}

export interface FilteredProduct {
	title: string;
	reason: string;
	keyword: string;
	filterCategory?: string;
}

export interface StoreStats {
	name: string;
	url: string;
	platform: string;
	fetched: number;
	filtered: number;
	final: number;
	inStock: number;
	outOfStock: number;
	duration: number;
	error: string | null;
	cached_at?: string;
	logs: LogEntry[];
	filteredProducts?: FilteredProduct[];
}

export interface Stats {
	lastUpdated: string;
	duration: number;
	stores: StoreStats[];
}

// Item-level types (for tracker)
export interface Item {
	id: string;
	storeId: string;
	productId: string;
	variantId: string;
	title: string;
	sku: string | null;
	price: number;
	regularPrice: number | null;
	image: string | null;
	url: string;
	vendor: string;
	category: string;
	tags: string[];
	inStock: boolean;
}

export interface ItemsData {
	lastUpdated: string;
	items: {
		[itemId: string]: Item;
	};
}

export interface ItemHistoryData {
	lastUpdated: string;
	history: {
		[itemId: string]: PricePoint[];
	};
}

// Data provider interface for abstraction
export interface DataProvider {
	getProducts(): Promise<ProductsData>;
	getTrackerData(): Promise<TrackerDataResponse>;
	getItems(): Promise<ItemsData>;
	getItemHistory(): Promise<ItemHistoryData>;
	getStats(): Promise<Stats>;
}
