"""
Test script to verify API key authentication works
"""
from orderbook_cache import orderbook_cache
import os

# Verify API key is loaded
print(f"API Key loaded: {'Yes' if orderbook_cache.api_key else 'No'}")
print(f"API Key (first 10 chars): {orderbook_cache.api_key[:10]}..." if orderbook_cache.api_key else "No API key")

# Test 1: Try to get token_id for a simple market
print("\nTest 1: Getting token_id for a market...")
market_name = "Will Bitcoin hit $100k in 2024?"
side = "Yes"

token_id = orderbook_cache.get_token_id_from_market(market_name, side)
print(f"Market: {market_name}")
print(f"Side: {side}")
print(f"Token ID: {token_id}")

if token_id:
    print("\n✓ Success! API authentication is working")

    # Test 2: Fetch orderbook data
    print("\nTest 2: Fetching orderbook data...")
    data = orderbook_cache.fetch_orderbook_data(token_id)
    if data:
        print(f"Bid: {data['best_bid']:.3f}")
        print(f"Ask: {data['best_ask']:.3f}")
        print(f"Spread: {data['spread']:.3f} ({data['spread_percentage']:.2f}%)")
        print("\n✓ Orderbook data fetched successfully!")
    else:
        print("✗ Failed to fetch orderbook data")
else:
    print("\n✗ Failed to get token_id - API authentication may still have issues")
