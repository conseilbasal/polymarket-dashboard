"""
Check Railway copy-trading actions for Abraham Accords
"""
import requests
import json

API_URL = "https://web-production-62f43.up.railway.app"
PASSWORD = "@@@TestApp@@@"

print("=" * 80)
print("CHECKING RAILWAY COPY-TRADING ACTIONS")
print("=" * 80)

# Login
print("\n1. Logging in...")
login_response = requests.post(
    f"{API_URL}/api/auth/login",
    json={"password": PASSWORD}
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("   [OK] Logged in")

# Check copy-trading comparison
print("\n2. Fetching copy-trading comparison...")
comparison_response = requests.get(
    f"{API_URL}/api/copy-trading/comparison",
    headers=headers
)

if comparison_response.status_code == 200:
    data = comparison_response.json()

    print(f"   [OK] Response received")
    print(f"   Target trader: {data.get('target_trader')}")
    print(f"   Total actions: {data.get('actions_count', 0)}")

    actions = data.get('actions', [])
    print(f"\n3. Checking {len(actions)} copy trading actions...")

    # Look for Abraham Accords
    found = False
    for action in actions:
        if 'Abraham Accords' in action.get('market', ''):
            found = True
            print(f"\n   [FOUND] Abraham Accords position!")
            print(f"   Market: {action.get('market')}")
            print(f"   Side: {action.get('side')}")
            print(f"   Action: {action.get('action')}")
            print(f"   Previous size: {action.get('previous_size', 0)}")
            print(f"   Current size: {action.get('current_size', 0)}")
            print(f"   Size delta: {action.get('size_delta', 0)}")
            print(f"   Your current size: {action.get('your_current_size', 0)}")
            print(f"   Recommended action: {action.get('recommended_action')}")
            print(f"   Shares to trade: {action.get('shares_to_trade', 0)}")

            # Verify
            current_size = float(action.get('current_size', 0))
            if current_size > 400:
                print(f"\n   ✅ PAGINATION FIX WORKING!")
                print(f"      Trader has {current_size:.2f} shares (was missing before)")
            else:
                print(f"\n   ❌ Unexpected size: {current_size:.2f}")
            break

    if not found:
        print("\n   ❌ Abraham Accords position NOT found in actions")
        print("\n   First 5 actions:")
        for i, action in enumerate(actions[:5]):
            print(f"      {i+1}. {action.get('market')} - {action.get('side')} - {action.get('current_size')} shares - {action.get('action')}")

        # Check if any have been added recently
        print(f"\n   Looking for NEW positions (action = 'OPEN')...")
        new_positions = [a for a in actions if a.get('action') == 'OPEN']
        print(f"   Found {len(new_positions)} new positions to open")
        for i, action in enumerate(new_positions[:3]):
            print(f"      {i+1}. {action.get('market')} - {action.get('side')} - {action.get('current_size')} shares")

else:
    print(f"   [ERROR] Failed: {comparison_response.status_code}")
    print(f"   Response: {comparison_response.text[:500]}")

print("\n" + "=" * 80)
