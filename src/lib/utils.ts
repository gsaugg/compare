// Re-export utilities for shadcn-svelte components
export { cn } from './utils/index';

// Type utilities for shadcn-svelte components
import type { Snippet } from 'svelte';

export type WithElementRef<T, El extends HTMLElement = HTMLElement> = T & {
	ref?: El | null;
};

export type WithoutChildrenOrChild<T> = T extends { children?: Snippet; child?: Snippet }
	? Omit<T, 'children' | 'child'>
	: T;
