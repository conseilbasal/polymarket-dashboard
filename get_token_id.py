"""
Get a valid token_id from Railway database
"""
import requests

API_URL = "https://web-production-62f43.up.railway.app"
PASSWORD = "@@@TestApp@@@"

# Login
login_response = requests.post(
    f"{API_URL}/api/auth/login",
    json={"password": PASSWORD}
)
token = login_response.json()["access_token"]

# Get positions data
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{API_URL}/api/positions", headers=headers)
data = response.json()

print("Positions de 25usdc dans Railway:")
print("=" * 80)

# Look for positions with market_id
if 'data' in data:
    for pos in data['data'][:5]:
        print(f"\nMarket: {pos.get('market', 'N/A')}")
        print(f"  Side: {pos.get('side', 'N/A')}")
        print(f"  Market ID: {pos.get('market_id', 'N/A')}")
        print(f"  Token ID: {pos.get('token_id', 'N/A')}")
        print(f"  Size: {pos.get('size', 0)}")
