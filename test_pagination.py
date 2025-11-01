"""
Test scheduler with pagination to verify all positions are fetched
"""
import sys
sys.path.append('.')

from scheduler import fetch_polymarket_positions

print("Testing pagination - fetching ALL positions for all traders...")
print("=" * 80)

fetch_polymarket_positions()

print("\n" + "=" * 80)
print("Done! Check the latest snapshot to verify all positions are present.")
