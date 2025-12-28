"""
Squarespace store fetcher.
"""

import json
from typing import Any

import requests

from fetchers.base import BaseFetcher


class SquarespaceFetcher(BaseFetcher):
    """Fetcher for Squarespace stores using the /store?format=json endpoint."""

    def __init__(self, store_name: str, base_url: str):
        super().__init__(store_name, base_url)
        self.page_size = 20
        self.offset = 0

    @property
    def platform_name(self) -> str:
        return "squarespace"

    def _build_page_url(self, page: int) -> str:
        # Squarespace uses offset-based pagination
        url = f"{self.base_url}/store?format=json&offset={self.offset}"
        self.offset += self.page_size  # Increment for next call
        return url

    def _extract_products(self, data: Any) -> list:
        return data.get("items", [])

    def _parse_response(self, response: requests.Response) -> Any:
        """Parse Squarespace response, handling potential extra content after JSON."""
        return self._extract_json(response.text)

    def _extract_json(self, text: str) -> dict:
        """
        Extract JSON from Squarespace response.

        Squarespace may include extra content after JSON, so we need to
        find the actual JSON boundary by counting braces.
        """
        # First try normal JSON parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Fall back to brace-counting for malformed responses
        brace_count = 0
        end_index = 0

        for i, char in enumerate(text):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            if brace_count == 0 and i > 0:
                end_index = i + 1
                break

        if end_index > 0:
            return json.loads(text[:end_index])

        # Last resort: raise error
        raise json.JSONDecodeError("Could not find valid JSON", text, 0)

    def _log_page_progress(self, page: int, count: int) -> None:
        """Log with offset instead of page number."""
        self.log.info(f"Offset {self.offset - self.page_size}: {count} products")
