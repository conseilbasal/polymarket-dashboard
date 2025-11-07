"""
Debug script to see what get_simplified_markets() returns
"""
from py_clob_client.client import ClobClient
import json

client = ClobClient("https://clob.polymarket.com")

print("Fetching markets...")
markets = client.get_simplified_markets()

print(f"\nType: {type(markets)}")
print(f"Length: {len(markets)}")

if markets:
    print(f"\nFirst market type: {type(markets[0])}")
    print(f"First market: {json.dumps(markets[0], indent=2)[:500]}")
