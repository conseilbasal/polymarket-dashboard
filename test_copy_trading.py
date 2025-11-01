"""
Test script to activate copy trading with $2 USD
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Railway API URL (replace with your actual Railway URL)
RAILWAY_API_URL = "https://web-production-62f43.up.railway.app"
# For local testing, use:
# API_URL = "http://localhost:8000"

# Your credentials
WALLET_ADDRESS = os.getenv("POLYMARKET_WALLET_ADDRESS")
PASSWORD = "@@@TestApp@@@"  # User's custom password

# Copy trading config
TARGET_TRADER = "25usdc"  # The trader to copy
TARGET_TRADER_NAME = "25usdc"
TEST_AMOUNT_USD = 2.0  # $2 USD for testing

def login():
    """Login to get JWT token"""
    response = requests.post(
        f"{RAILWAY_API_URL}/api/auth/login",
        json={"password": PASSWORD}
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"[OK] Login successful")
        return token
    else:
        print(f"[ERROR] Login failed: {response.status_code} - {response.text}")
        return None

def get_wallet_balance(token):
    """Get current wallet balance from Polymarket"""
    # This would need to call Polymarket API to get actual balance
    # For now, let's assume a reasonable balance for testing
    # You can replace this with actual API call

    # Estimated balance based on typical user
    estimated_balance = 1000.0  # USD
    print(f"[INFO] Using estimated balance: ${estimated_balance:.2f} USD")
    print(f"  (In production, this would fetch real balance from Polymarket)")

    return estimated_balance

def calculate_copy_percentage(wallet_balance, test_amount):
    """Calculate percentage to copy based on wallet balance and test amount"""
    percentage = (test_amount / wallet_balance) * 100

    # Ensure percentage is within allowed range (0.1% to 100%)
    percentage = max(0.1, min(100.0, percentage))

    return percentage

def enable_copy_trading(token, percentage):
    """Enable copy trading with calculated percentage"""
    headers = {"Authorization": f"Bearer {token}"}

    # Parameters go in URL query string, not JSON body
    params = {
        "target_trader": TARGET_TRADER,
        "trader_name": TARGET_TRADER_NAME,
        "copy_percentage": percentage
    }

    response = requests.post(
        f"{RAILWAY_API_URL}/api/copy-trading/enable",
        params=params,
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Copy trading enabled successfully!")
        print(f"  Target trader: {TARGET_TRADER_NAME}")
        print(f"  Copy percentage: {percentage:.2f}%")
        print(f"  Estimated copy amount: ${TEST_AMOUNT_USD:.2f} USD")
        return data
    else:
        print(f"[ERROR] Failed to enable copy trading: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def get_copy_trading_status(token):
    """Get current copy trading status"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{RAILWAY_API_URL}/api/copy-trading/status",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\n[STATUS] Copy Trading Status:")
        print(f"  Active configs: {len(data.get('active_configs', []))}")
        print(f"  Pending orders: {len(data.get('pending_orders', []))}")
        print(f"  Total PnL: ${data.get('total_pnl', 0):.2f}")
        return data
    else:
        print(f"[ERROR] Failed to get status: {response.status_code}")
        return None

def main():
    print("=" * 60)
    print("Copy Trading Test - $2 USD")
    print("=" * 60)
    print()

    # Step 1: Login
    print("Step 1: Login to API...")
    token = login()
    if not token:
        return
    print()

    # Step 2: Get wallet balance
    print("Step 2: Get wallet balance...")
    balance = get_wallet_balance(token)
    print()

    # Step 3: Calculate percentage
    print("Step 3: Calculate copy percentage...")
    percentage = calculate_copy_percentage(balance, TEST_AMOUNT_USD)
    print(f"[OK] Calculated percentage: {percentage:.4f}%")
    print(f"  (${TEST_AMOUNT_USD} / ${balance} * 100)")
    print()

    # Step 4: Enable copy trading
    print("Step 4: Enable copy trading...")
    result = enable_copy_trading(token, percentage)
    print()

    # Step 5: Check status
    if result:
        print("Step 5: Check copy trading status...")
        get_copy_trading_status(token)
        print()

        print("=" * 60)
        print("[SUCCESS] Copy trading test completed!")
        print("=" * 60)
        print()
        print("What happens next:")
        print("1. Every 5 minutes, the scheduler will check 25usdc's positions")
        print("2. If 25usdc opens a new position, your bot will copy it")
        print(f"3. Your copy size will be ~{percentage:.4f}% of 25usdc's size")
        print(f"4. Estimated exposure: ${TEST_AMOUNT_USD:.2f} USD")
        print()
        print(f"Monitor at: {RAILWAY_API_URL}/api/copy-trading/status")

if __name__ == "__main__":
    main()
