"""
Verify pagination fix is working on Railway
Check if Abraham Accords position is now correctly detected
"""
import requests
import time

API_URL = "https://web-production-62f43.up.railway.app"
PASSWORD = "@@@TestApp@@@"

print("=" * 80)
print("VERIFYING PAGINATION FIX ON RAILWAY")
print("=" * 80)

# Login
print("\n1. Logging in...")
try:
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"password": PASSWORD},
        timeout=10
    )
    if login_response.status_code != 200:
        print(f"   [ERROR] Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        exit(1)

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   [OK] Logged in successfully")
except Exception as e:
    print(f"   [ERROR] {str(e)}")
    exit(1)

# Wait for Railway deployment
print("\n2. Waiting 30 seconds for Railway deployment to complete...")
time.sleep(30)

# Check copy trading activity
print("\n3. Checking copy trading activity...")
try:
    activity_response = requests.get(
        f"{API_URL}/api/copy-trading/activity",
        headers=headers,
        timeout=10
    )

    if activity_response.status_code != 200:
        print(f"   [ERROR] Failed to fetch activity: {activity_response.status_code}")
        print(f"   Response: {activity_response.text}")
        exit(1)

    data = activity_response.json()
    print(f"   [OK] Fetched {len(data.get('data', []))} activity items")
except Exception as e:
    print(f"   [ERROR] {str(e)}")
    exit(1)

# Find Abraham Accords market
print("\n4. Searching for Abraham Accords market...")
found = False
for item in data.get('data', []):
    if 'Abraham Accords' in item.get('market', ''):
        found = True
        print(f"\n   [FOUND] Abraham Accords market detected!")
        print(f"   Market: {item.get('market')}")
        print(f"   Side: {item.get('side')}")
        print(f"   Action: {item.get('action')}")
        print(f"   Current size (trader): {item.get('current_size', 0)}")
        print(f"   Your current size: {item.get('your_current_size', 0)}")
        print(f"   Recommended action: {item.get('recommended_action')}")
        print(f"   Shares to trade: {item.get('shares_to_trade', 0)}")

        # Verify the fix
        current_size = float(item.get('current_size', 0))
        if current_size > 400:  # Should be ~500 shares
            print(f"\n   ✅ VERIFICATION PASSED!")
            print(f"      Trader has {current_size:.2f} shares (pagination working correctly)")
        else:
            print(f"\n   ❌ VERIFICATION FAILED!")
            print(f"      Expected ~500 shares, got {current_size:.2f}")
        break

if not found:
    print("\n   ❌ Abraham Accords market NOT found!")
    print("   This could mean:")
    print("   - Railway deployment hasn't completed yet")
    print("   - Scheduler hasn't run yet (runs every 5 minutes)")
    print("   - Position detection engine hasn't processed new data yet")
    print("\n   Try running this script again in 5 minutes.")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
