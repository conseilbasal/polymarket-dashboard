"""
Test manual refresh of orderbook cache
"""
from orderbook_cache import orderbook_cache
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)

print("Starting manual orderbook cache refresh...")
print("This will take a few minutes depending on the number of markets...")
print()

try:
    orderbook_cache.refresh_all_active_markets()
    print("\nRefresh completed!")
except Exception as e:
    print(f"\nError during refresh: {e}")
    import traceback
    traceback.print_exc()
