"""
Debug script to see the structure of get_simplified_markets()
"""
from py_clob_client.client import ClobClient
import json

client = ClobClient("https://clob.polymarket.com")

print("Fetching markets...")
markets = client.get_simplified_markets()

print(f"\nType: {type(markets)}")
print(f"\nKeys: {list(markets.keys())}")

for key in markets.keys():
    print(f"\n{key}:")
    print(f"  Type: {type(markets[key])}")
    if isinstance(markets[key], list):
        print(f"  Length: {len(markets[key])}")
        if markets[key]:
            print(f"  First item: {json.dumps(markets[key][0], indent=2)[:300]}")
