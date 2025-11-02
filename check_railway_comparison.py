"""
Check Railway copy-trading comparison endpoint for Abraham Accords
"""
import requests

API_URL = "https://web-production-62f43.up.railway.app"
PASSWORD = "@@@TestApp@@@"

print("=" * 80)
print("CHECKING RAILWAY COPY-TRADING COMPARISON")
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

    # Check if 25usdc trader exists
    if '25usdc' in data:
        trader_data = data['25usdc']
        print(f"   [OK] Found 25usdc trader data")
        print(f"   Total positions: {len(trader_data.get('positions', []))}")

        # Look for Abraham Accords
        print("\n3. Searching for Abraham Accords market...")
        found = False
        for pos in trader_data.get('positions', []):
            if 'Abraham Accords' in pos.get('market', ''):
                found = True
                print(f"\n   [FOUND] Abraham Accords position!")
                print(f"   Market: {pos.get('market')}")
                print(f"   Side: {pos.get('side')}")
                print(f"   Trader size: {pos.get('trader_size')}")
                print(f"   Your size: {pos.get('your_size')}")
                print(f"   Delta: {pos.get('delta')}")
                print(f"   Action: {pos.get('action')}")

                # Verify
                trader_size = float(pos.get('trader_size', 0))
                if trader_size > 400:
                    print(f"\n   ✅ PAGINATION FIX WORKING!")
                    print(f"      Trader has {trader_size:.2f} shares (was missing before)")
                else:
                    print(f"\n   ❌ Unexpected size: {trader_size:.2f}")
                break

        if not found:
            print("\n   ❌ Abraham Accords position NOT found")
            print("\n   First 5 positions:")
            for i, pos in enumerate(trader_data.get('positions', [])[:5]):
                print(f"      {i+1}. {pos.get('market')} - {pos.get('side')} - {pos.get('trader_size')} shares")

        total_positions = len(trader_data.get('positions', []))
        print(f"\n   Total positions for 25usdc: {total_positions}")
        if total_positions > 100:
            print(f"   ✅ Pagination working ({total_positions} positions)")
        else:
            print(f"   ⚠️  Only {total_positions} positions")
    else:
        print(f"   [ERROR] 25usdc trader not found in response")
        print(f"   Available traders: {list(data.keys())}")
else:
    print(f"   [ERROR] Failed: {comparison_response.status_code}")
    print(f"   Response: {comparison_response.text}")

print("\n" + "=" * 80)
