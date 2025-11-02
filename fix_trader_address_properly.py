"""
Fix the copy trading configuration to use the actual wallet address
"""

import os
from sqlalchemy import create_engine, text

# Railway database URL
DATABASE_URL = "postgresql://postgres:osDFUPPrdSKBBGfpAEldJCSqXZJvmqRC@centerbeam.proxy.rlwy.net:58371/railway"

# Correct address from traders.json (confirmed by user)
CORRECT_ADDRESS = "0x75e765216a57942d738d880ffcda854d9f869080"

print("=" * 80)
print("Fixing copy trading configuration to use actual wallet address")
print("=" * 80)

engine = create_engine(DATABASE_URL)

# Check current configuration
print("\n1. Current copy trading config:")
with engine.connect() as conn:
    query = text("""
        SELECT id, user_wallet_address, target_trader_address, target_trader_name, copy_percentage, enabled
        FROM copy_trading_config
    """)
    result = conn.execute(query)
    rows = result.fetchall()

    if rows:
        for row in rows:
            print(f"\n  Config #{row.id}:")
            print(f"    User: {row.user_wallet_address}")
            print(f"    Target Address: {row.target_trader_address}")
            print(f"    Target Name: {row.target_trader_name}")
            print(f"    Copy %: {row.copy_percentage}%")
            print(f"    Enabled: {row.enabled}")

            if row.target_trader_address == "25usdc":
                print(f"    ❌ USING NAME INSTEAD OF ADDRESS!")
    else:
        print("  No config found!")

# Update to use the actual wallet address
print(f"\n2. Updating target_trader_address to: {CORRECT_ADDRESS}")
with engine.connect() as conn:
    query = text("""
        UPDATE copy_trading_config
        SET target_trader_address = :correct_address
        WHERE target_trader_name = '25usdc'
    """)

    result = conn.execute(query, {
        "correct_address": CORRECT_ADDRESS
    })

    conn.commit()

    print(f"  Updated {result.rowcount} row(s)")

# Verify the update
print("\n3. Verifying updated config:")
with engine.connect() as conn:
    query = text("""
        SELECT id, user_wallet_address, target_trader_address, target_trader_name, copy_percentage, enabled
        FROM copy_trading_config
    """)
    result = conn.execute(query)
    rows = result.fetchall()

    if rows:
        for row in rows:
            print(f"\n  Config #{row.id}:")
            print(f"    User: {row.user_wallet_address}")
            print(f"    Target Address: {row.target_trader_address}")
            print(f"    Target Name: {row.target_trader_name}")
            print(f"    Copy %: {row.copy_percentage}%")
            print(f"    Enabled: {row.enabled}")

            if row.target_trader_address == CORRECT_ADDRESS:
                print(f"    ✅ CORRECT WALLET ADDRESS!")

print("\n" + "=" * 80)
print("✅ Configuration fixed!")
print("")
print("The copy trading bot will now:")
print(f"  1. Fetch positions from: {CORRECT_ADDRESS}")
print("  2. Detect when 25usdc opens/closes positions")
print("  3. Automatically copy 5% of each position")
print("")
print("Next check: Within 5 minutes")
print("=" * 80)
