"""
Log collector for capturing scraper logs per store.
"""

import logging
import re
from datetime import datetime, timezone
from collections import defaultdict
import threading


class StoreLogCollector(logging.Handler):
    """Custom logging handler that captures logs per store."""

    def __init__(self):
        super().__init__()
        self.logs = defaultdict(list)  # store_name -> list of log entries
        self._lock = threading.Lock()

        # Pattern to extract store name from log messages
        # Primary: "Store Name: message" (from StoreLoggerAdapter)
        # Fallback patterns for scrape.py logs
        self._store_patterns = [
            re.compile(r"^([^:]+): "),  # "Store Name: message"
            re.compile(r"Fetching from ([^.]+)\.\.\."),
            re.compile(r"products from ([^.]+)$"),
            re.compile(r"Error fetching ([^ ]+)"),
        ]

    def _extract_store(self, message: str) -> str | None:
        """Try to extract store name from log message."""
        for pattern in self._store_patterns:
            match = pattern.search(message)
            if match:
                return match.group(1).strip()
        return None

    def emit(self, record: logging.LogRecord):
        """Capture a log record."""
        message = record.getMessage()

        # Try to extract store from message
        store = self._extract_store(message)

        if store is None:
            store = "_global"
        else:
            # Strip the store prefix from message if present
            prefix = f"{store}: "
            if message.startswith(prefix):
                message = message[len(prefix):]

        # Format timestamp as time only (HH:MM:SS)
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")

        entry = {
            "time": timestamp,
            "level": record.levelname,
            "message": message
        }

        with self._lock:
            self.logs[store].append(entry)

    def get_logs_for_store(self, store_name: str) -> list:
        """Get all log entries for a specific store."""
        with self._lock:
            return list(self.logs.get(store_name, []))


# Global instance
_collector = None


def get_collector() -> StoreLogCollector:
    """Get or create the global log collector instance."""
    global _collector
    if _collector is None:
        _collector = StoreLogCollector()
        _collector.setLevel(logging.DEBUG)
        # Add to root logger
        logging.getLogger().addHandler(_collector)
    return _collector


def get_store_logs(store_name: str) -> list:
    """Get logs for a specific store."""
    return get_collector().get_logs_for_store(store_name)
