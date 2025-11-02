"""
Test script to check if we can detect 25usdc positions
"""

import requests
import json
from datetime import datetime

# 25usdc trader address
TRADER_ADDRESS = "0x00ce0682efd980b2caa0e8d7f7e5290fe4f9df0f"

print("=" * 80)
print(f"Testing position detection for 25usdc")
print(f"Address: {TRADER_ADDRESS}")
print(f"Time: {datetime.now()}")
print("=" * 80)

# Fetch current positions
url = f"https://data-api.polymarket.com/positions?user={TRADER_ADDRESS}"
print(f"\nFetching positions from: {url}\n")

response = requests.get(url, timeout=10)

print(f"Status code: {response.status_code}")

if response.status_code == 200:
    positions_data = response.json()

    print(f"\nTotal positions found: {len(positions_data)}")
    print("\n" + "=" * 80)

    # Display last 5 positions (sorted by most recent)
    for idx, pos in enumerate(positions_data[:10]):
        print(f"\nPosition #{idx + 1}:")
        print(f"  Market: {pos.get('market_slug', 'N/A')}")
        print(f"  Market ID: {pos.get('market', 'N/A')}")
        print(f"  Token ID: {pos.get('asset_id', 'N/A')}")
        print(f"  Side: {pos.get('outcome', 'N/A')}")
        print(f"  Size: {pos.get('size', 0)} shares")
        print(f"  Avg Price: ${pos.get('avg_price', 0):.4f}")
        print(f"  Value: ${pos.get('value', 0):.2f}")

        # Check if this matches the positions the user mentioned
        market_name = pos.get('market_slug', '').lower()
        if 'venezuela' in market_name:
            print(f"  ⚠️  VENEZUELA POSITION DETECTED!")
        elif 'bitcoin' in market_name or '100k' in market_name or '120k' in market_name:
            print(f"  ⚠️  BITCOIN POSITION DETECTED!")

    print("\n" + "=" * 80)

    # Check for the specific positions the user mentioned
    print("\nSearching for specific positions mentioned by user...")

    venezuela_found = False
    bitcoin_found = False

    for pos in positions_data:
        market_name = pos.get('market_slug', '').lower()

        if 'venezuela' in market_name and 'military' in market_name:
            venezuela_found = True
            print(f"\n✅ FOUND: Venezuela military position")
            print(f"   Size: {pos.get('size')} shares")
            print(f"   Price: ${pos.get('avg_price'):.4f}")
            print(f"   Value: ${pos.get('value'):.2f}")

        if ('bitcoin' in market_name or 'btc' in market_name) and ('100k' in market_name or '120k' in market_name):
            bitcoin_found = True
            print(f"\n✅ FOUND: Bitcoin 100k/120k position")
            print(f"   Size: {pos.get('size')} shares")
            print(f"   Price: ${pos.get('avg_price'):.4f}")
            print(f"   Value: ${pos.get('value'):.2f}")

    if not venezuela_found:
        print("\n❌ Venezuela position NOT found")

    if not bitcoin_found:
        print("\n❌ Bitcoin position NOT found")

    print("\n" + "=" * 80)
    print("\nFull JSON response saved to 'positions_debug.json'")

    # Save full response for debugging
    with open("positions_debug.json", "w") as f:
        json.dump(positions_data, f, indent=2)

else:
    print(f"Error: {response.text}")
