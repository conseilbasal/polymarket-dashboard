"""
Debug position detection for Abraham Accords market
"""
import requests

API_URL = "https://web-production-62f43.up.railway.app"
PASSWORD = "@@@TestApp@@@"

# Login
print("Logging in...")
login_response = requests.post(
    f"{API_URL}/api/auth/login",
    json={"password": PASSWORD}
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get copy trading activity
print("\nFetching copy trading activity...")
activity_response = requests.get(
    f"{API_URL}/api/copy-trading/activity",
    headers=headers
)

if activity_response.status_code == 200:
    data = activity_response.json()

    # Find Abraham Accords market
    print("\n" + "="*80)
    print("ABRAHAM ACCORDS MARKET:")
    print("="*80)

    for item in data.get('data', []):
        if 'Abraham Accords' in item.get('market', ''):
            print(f"\nMarket: {item.get('market')}")
            print(f"Side: {item.get('side')}")
            print(f"Action: {item.get('action')}")
            print(f"Previous size: {item.get('previous_size', 0)}")
            print(f"Current size: {item.get('current_size', 0)}")
            print(f"Size delta: {item.get('size_delta', 0)}")
            print(f"Your current size: {item.get('your_current_size', 0)}")
            print(f"Recommended action: {item.get('recommended_action')}")
            print(f"Shares to trade: {item.get('shares_to_trade', 0)}")
else:
    print(f"Error: {activity_response.status_code}")
    print(activity_response.text)

# Also check positions_history directly
print("\n" + "="*80)
print("CHECKING positions_history TABLE:")
print("="*80)

check_response = requests.get(
    f"{API_URL}/api/debug/positions-history?user=25usdc&market=Abraham",
    headers=headers
)

if check_response.status_code == 200:
    print(check_response.text)
else:
    print("No debug endpoint available")
