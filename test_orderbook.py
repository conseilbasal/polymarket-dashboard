"""
Test script to verify orderbook cache functionality
"""
from orderbook_cache import orderbook_cache
from database import engine
from sqlalchemy import text

# Test 1: Get token_id
print("Test 1: Getting token_id for a market...")
market_name = "Will Trump win the 2024 election?"
side = "Yes"

token_id = orderbook_cache.get_token_id_from_market(market_name, side)
print(f"Token ID: {token_id}")

if token_id:
    # Test 2: Fetch orderbook data
    print("\nTest 2: Fetching orderbook data...")
    data = orderbook_cache.fetch_orderbook_data(token_id)
    print(f"Orderbook data: {data}")

    # Test 3: Update cache
    print("\nTest 3: Updating cache...")
    orderbook_cache.update_market_orderbook(market_name, side)

    # Test 4: Retrieve from cache
    print("\nTest 4: Retrieving from cache...")
    cached = orderbook_cache.get_orderbook_for_market(market_name, side)
    print(f"Cached data: {cached}")
else:
    print("Could not find token_id - trying with actual market from positions_history")

    # Query positions_history for actual markets
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT market, side
            FROM positions_history
            WHERE timestamp > datetime('now', '-1 hour')
            LIMIT 1
        """))
        row = result.fetchone()

        if row:
            market_name = row[0]
            side = row[1]
            print(f"\nTrying with actual market: {market_name} ({side})")

            token_id = orderbook_cache.get_token_id_from_market(market_name, side)
            print(f"Token ID: {token_id}")

            if token_id:
                data = orderbook_cache.fetch_orderbook_data(token_id)
                print(f"Orderbook data: {data}")

                orderbook_cache.update_market_orderbook(market_name, side)
                cached = orderbook_cache.get_orderbook_for_market(market_name, side)
                print(f"Cached data: {cached}")
        else:
            print("No recent positions found in positions_history")
