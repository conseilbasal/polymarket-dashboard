"""
Test script to manually trigger orderbook refresh
"""
from orderbook_cache import orderbook_cache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 60)
print("Manual Orderbook Refresh Test")
print("=" * 60)

print("\nRefreshing orderbook data for all active markets...")
print("This will fetch bid/ask/spread data from Polymarket CLOB API")
print("and cache it in the database.")
print()

orderbook_cache.refresh_all_active_markets()

print("\n" + "=" * 60)
print("Refresh complete!")
print("=" * 60)
