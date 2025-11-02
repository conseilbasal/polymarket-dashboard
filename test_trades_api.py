"""
Test different Polymarket APIs to find the trades/transactions endpoint
"""

import requests
import json
from datetime import datetime

TRADER_ADDRESS = "0x00ce0682efd980b2caa0e8d7f7e5290fe4f9df0f"

print("=" * 80)
print(f"Testing different Polymarket APIs for 25usdc")
print(f"Address: {TRADER_ADDRESS}")
print("=" * 80)

# API 1: Positions (already tested - returns 0)
print("\n1. Testing /positions API...")
url1 = f"https://data-api.polymarket.com/positions?user={TRADER_ADDRESS}"
print(f"URL: {url1}")
response1 = requests.get(url1, timeout=10)
print(f"Status: {response1.status_code}")
print(f"Positions found: {len(response1.json()) if response1.status_code == 200 else 'ERROR'}")

# API 2: Try trades/transactions endpoint
print("\n2. Testing /trades API...")
url2 = f"https://data-api.polymarket.com/trades?user={TRADER_ADDRESS}&limit=10"
print(f"URL: {url2}")
try:
    response2 = requests.get(url2, timeout=10)
    print(f"Status: {response2.status_code}")
    if response2.status_code == 200:
        trades = response2.json()
        print(f"Trades found: {len(trades)}")
        if trades:
            print("\nRecent trades:")
            for i, trade in enumerate(trades[:5]):
                print(f"\n  Trade #{i+1}:")
                print(f"    Market: {trade.get('market', 'N/A')}")
                print(f"    Side: {trade.get('side', 'N/A')}")
                print(f"    Size: {trade.get('size', 'N/A')}")
                print(f"    Price: ${trade.get('price', 0):.4f}")
                print(f"    Timestamp: {trade.get('timestamp', 'N/A')}")

            # Save full response
            with open("trades_debug.json", "w") as f:
                json.dump(trades, f, indent=2)
            print("\nFull response saved to 'trades_debug.json'")
    else:
        print(f"Response: {response2.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

# API 3: Try events endpoint
print("\n3. Testing /events API...")
url3 = f"https://data-api.polymarket.com/events?user={TRADER_ADDRESS}&limit=10"
print(f"URL: {url3}")
try:
    response3 = requests.get(url3, timeout=10)
    print(f"Status: {response3.status_code}")
    if response3.status_code == 200:
        print(f"Events found: {len(response3.json())}")
    else:
        print(f"Response: {response3.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

# API 4: Try history endpoint
print("\n4. Testing /history API...")
url4 = f"https://data-api.polymarket.com/history?user={TRADER_ADDRESS}&limit=10"
print(f"URL: {url4}")
try:
    response4 = requests.get(url4, timeout=10)
    print(f"Status: {response4.status_code}")
    if response4.status_code == 200:
        print(f"History items found: {len(response4.json())}")
    else:
        print(f"Response: {response4.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

# API 5: Try the Gamma Markets API (used by the official Polymarket site)
print("\n5. Testing Gamma Markets API...")
url5 = f"https://gamma-api.polymarket.com/positions?user={TRADER_ADDRESS}"
print(f"URL: {url5}")
try:
    response5 = requests.get(url5, timeout=10)
    print(f"Status: {response5.status_code}")
    if response5.status_code == 200:
        positions = response5.json()
        print(f"Positions found: {len(positions)}")
        if positions:
            print("\nPositions:")
            for i, pos in enumerate(positions[:5]):
                print(f"\n  Position #{i+1}:")
                print(f"    Market: {pos.get('market', 'N/A')}")
                print(f"    Size: {pos.get('size', 'N/A')}")

            # Save full response
            with open("gamma_positions_debug.json", "w") as f:
                json.dump(positions, f, indent=2)
            print("\nFull response saved to 'gamma_positions_debug.json'")
    else:
        print(f"Response: {response5.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 80)
print("Testing complete!")
print("=" * 80)
