"""
Test script to place a 2 EUR limit order on Railway
Gets a market token_id and calls the /api/test-order endpoint
"""

import requests

# Railway API
API_URL = "https://web-production-62f43.up.railway.app"
PASSWORD = "@@@TestApp@@@"

print("="*80)
print("TEST: Place a 2 EUR limit order on Railway")
print("="*80)

# Step 1: Login
print("\n1. Logging in to Railway API...")
login_response = requests.post(
    f"{API_URL}/api/auth/login",
    json={"password": PASSWORD}
)

if login_response.status_code != 200:
    print(f"ERROR: Login failed - {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
print(f"   Login successful! Token: {token[:20]}...")

# Step 2: Use a known token_id from a popular market
# Using "Will Bitcoin hit $100k first" YES token
print("\n2. Using test market token_id...")
token_id = "21742633143463906290569050155826241533067272736897614950488156847949938836455"
market_title = "Will Bitcoin hit $100k or $120k first? (120k option)"
print(f"   Market: {market_title}")
print(f"   Token ID: {token_id[:20]}...{token_id[-10:]}")

# Step 3: Place test order
print("\n3. Placing 2 EUR limit order on Railway...")
print(f"   Market: {market_title}")
print(f"   Token ID: {token_id}")
print(f"   Price: $0.05 per share")
print(f"   Amount: $2.00 USD")

headers = {"Authorization": f"Bearer {token}"}
order_response = requests.post(
    f"{API_URL}/api/test-order",
    headers=headers,
    params={
        "token_id": token_id,
        "price": 0.05,  # 5 cents per share
        "amount_usd": 2.0  # 2 USD
    }
)

print(f"\n4. Response from Railway:")
print(f"   Status code: {order_response.status_code}")

if order_response.status_code == 200:
    result = order_response.json()
    print(f"\n   SUCCESS!")
    print(f"   Message: {result.get('message')}")
    print(f"   Order ID: {result['order_details'].get('order_id')}")
    print(f"   Size: {result['order_details'].get('size')} shares")
    print(f"   Price: ${result['order_details'].get('price')}")
    print(f"   Status: {result['order_details'].get('status')}")
else:
    print(f"\n   ERROR!")
    print(f"   Response: {order_response.text}")

print("\n" + "="*80)
print("Test complete!")
print("="*80)
