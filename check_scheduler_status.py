"""
Check when Railway scheduler last ran
"""
import requests
from datetime import datetime

API_URL = "https://web-production-62f43.up.railway.app"
PASSWORD = "@@@TestApp@@@"

print("=" * 80)
print("CHECKING RAILWAY SCHEDULER STATUS")
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

# Check scheduler status
print("\n2. Checking scheduler status...")
status_response = requests.get(
    f"{API_URL}/api/scheduler/status",
    headers=headers
)

if status_response.status_code == 200:
    data = status_response.json()
    print(f"   [OK] Scheduler status:")
    print(f"   Last run: {data.get('last_run', 'Never')}")
    print(f"   Status: {data.get('status', 'Unknown')}")
else:
    print(f"   [ERROR] Failed: {status_response.status_code}")

# Check latest positions timestamp
print("\n3. Checking latest positions timestamp...")
positions_response = requests.get(
    f"{API_URL}/api/positions/latest",
    headers=headers
)

if positions_response.status_code == 200:
    positions = positions_response.json()
    if positions:
        first_pos = positions[0]
        timestamp = first_pos.get('updated_at', 'Unknown')
        print(f"   [OK] Latest positions from: {timestamp}")

        # Parse timestamp to see how old it is
        try:
            if timestamp != 'Unknown':
                updated_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                now = datetime.now(updated_time.tzinfo) if updated_time.tzinfo else datetime.now()
                age_minutes = (now - updated_time).total_seconds() / 60
                print(f"   Age: {age_minutes:.1f} minutes old")

                if age_minutes < 10:
                    print(f"   [OK] Data is recent (< 10 minutes)")
                else:
                    print(f"   [WARNING] Data is {age_minutes:.1f} minutes old")
        except Exception as e:
            print(f"   Could not parse timestamp: {e}")

        # Check if we have 25usdc positions
        usdc_positions = [p for p in positions if p.get('user') == '25usdc']
        print(f"   Total 25usdc positions: {len(usdc_positions)}")

        # Look for Abraham Accords
        abraham = [p for p in usdc_positions if 'Abraham Accords' in p.get('market', '')]
        if abraham:
            pos = abraham[0]
            print(f"\n   [FOUND] Abraham Accords in database:")
            print(f"   Size: {pos.get('size')}")
            print(f"   Avg Price: {pos.get('avg_price')}")
            print(f"   Current Price: {pos.get('current_price')}")
        else:
            print(f"\n   [NOT FOUND] Abraham Accords not in latest positions")

else:
    print(f"   [ERROR] Failed: {positions_response.status_code}")

print("\n" + "=" * 80)
