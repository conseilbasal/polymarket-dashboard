"""
Test script for orderbook cache using py-clob-client
"""
from orderbook_cache import orderbook_cache
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

print("Testing Orderbook Cache with py-clob-client")
print("=" * 60)

# Test 1: Get all markets
print("\n1. Testing get_simplified_markets()...")
try:
    markets = orderbook_cache._get_all_markets()
    print(f"   SUCCESS: Retrieved {len(markets)} markets")
    if markets:
        print(f"   First market: {markets[0].get('question', 'N/A')[:60]}")
except Exception as e:
    print(f"   FAILED: {e}")

# Test 2: Search for a specific market from positions
print("\n2. Testing token_id lookup...")
import pandas as pd
from pathlib import Path

snapshots_dir = Path("data/snapshots")
snapshots = sorted(snapshots_dir.glob("positions_*.csv"))

if snapshots:
    df = pd.read_csv(snapshots[-1])
    test_market = df.iloc[0]['market']
    test_side = df.iloc[0]['side']

    print(f"   Market: {test_market[:60]}")
    print(f"   Side: {test_side}")

    try:
        token_id = orderbook_cache.get_token_id_from_market(test_market, test_side)
        if token_id:
            print(f"   SUCCESS: Found token_id = {token_id}")

            # Test 3: Get orderbook
            print("\n3. Testing orderbook fetch...")
            orderbook = orderbook_cache.fetch_orderbook_data(token_id)
            if orderbook:
                print(f"   SUCCESS:")
                print(f"      Best Bid: {orderbook['best_bid']:.4f}")
                print(f"      Best Ask: {orderbook['best_ask']:.4f}")
                print(f"      Spread: {orderbook['spread']:.4f} ({orderbook['spread_percentage']:.2f}%)")
            else:
                print(f"   No orderbook data available (market may be closed)")
        else:
            print(f"   FAILED: Could not find token_id")
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete!")
