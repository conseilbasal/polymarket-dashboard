"""
Debug to see the exact structure of markets
"""
from py_clob_client.client import ClobClient
import json

client = ClobClient("https://clob.polymarket.com")
markets_data = client.get_simplified_markets()
markets = markets_data.get('data', [])

print(f"Total markets: {len(markets)}")
print("\nFirst market structure:")
print(json.dumps(markets[0], indent=2)[:800])
