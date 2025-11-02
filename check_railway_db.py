"""
Check Railway database for Abraham Accords position
"""
import requests

API_URL = "https://web-production-62f43.up.railway.app"
PASSWORD = "@@@TestApp@@@"

print("=" * 80)
print("CHECKING RAILWAY DATABASE")
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

# Check positions endpoint
print("\n2. Fetching 25usdc positions from Railway database...")
positions_response = requests.get(
    f"{API_URL}/api/positions?user=25usdc",
    headers=headers
)

if positions_response.status_code == 200:
    positions = positions_response.json()
    print(f"   [OK] Fetched {len(positions)} positions for 25usdc")

    # Look for Abraham Accords
    print("\n3. Searching for Abraham Accords market...")
    found = False
    for pos in positions:
        if 'Abraham Accords' in pos.get('market', ''):
            found = True
            print(f"\n   [FOUND] Abraham Accords position!")
            print(f"   Market: {pos.get('market')}")
            print(f"   Side: {pos.get('side')}")
            print(f"   Size: {pos.get('size')}")
            print(f"   Avg Price: {pos.get('avg_price')}")
            print(f"   Current Price: {pos.get('current_price')}")
            print(f"   PnL: {pos.get('pnl')}")

            # Verify
            size = float(pos.get('size', 0))
            if size > 400:
                print(f"\n   ✅ PAGINATION FIX WORKING!")
                print(f"      Position has {size:.2f} shares (was missing before)")
            else:
                print(f"\n   ❌ Unexpected size: {size:.2f}")
            break

    if not found:
        print("\n   ❌ Abraham Accords position NOT found in database")
        print("   Showing first 5 positions:")
        for i, pos in enumerate(positions[:5]):
            print(f"      {i+1}. {pos.get('market')} - {pos.get('side')} - {pos.get('size')} shares")

    print(f"\n   Total positions for 25usdc: {len(positions)}")
    if len(positions) > 100:
        print(f"   ✅ Pagination working (fetched more than 100 positions)")
    else:
        print(f"   ⚠️  Only {len(positions)} positions (should be more)")

else:
    print(f"   [ERROR] Failed to fetch positions: {positions_response.status_code}")
    print(f"   Response: {positions_response.text}")

print("\n" + "=" * 80)
