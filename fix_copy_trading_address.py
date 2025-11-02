"""
Fix the copy trading configuration with the CORRECT 25usdc address
"""

import os
from sqlalchemy import create_engine, text

# Railway database URL
DATABASE_URL = "postgresql://postgres:osDFUPPrdSKBBGfpAEldJCSqXZJvmqRC@centerbeam.proxy.rlwy.net:58371/railway"

# Correct address from traders.json
CORRECT_ADDRESS = "0x75e765216a57942d738d880ffcda854d9f869080"
# Wrong address I was using
WRONG_ADDRESS = "0x00ce0682efd980b2caa0e8d7f7e5290fe4f9df0f"

print("=" * 80)
print("Fixing copy trading configuration")
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
            print(f"    Target: {row.target_trader_address}")
            print(f"    Name: {row.target_trader_name}")
            print(f"    Copy %: {row.copy_percentage}%")
            print(f"    Enabled: {row.enabled}")

            if row.target_trader_address == WRONG_ADDRESS:
                print(f"    ❌ WRONG ADDRESS DETECTED!")
    else:
        print("  No config found!")

# Update to correct address
print("\n2. Updating to correct address...")
with engine.connect() as conn:
    query = text("""
        UPDATE copy_trading_config
        SET target_trader_address = :correct_address
        WHERE target_trader_address = :wrong_address
    """)

    result = conn.execute(query, {
        "correct_address": CORRECT_ADDRESS,
        "wrong_address": WRONG_ADDRESS
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
            print(f"    Target: {row.target_trader_address}")
            print(f"    Name: {row.target_trader_name}")
            print(f"    Copy %: {row.copy_percentage}%")
            print(f"    Enabled: {row.enabled}")

            if row.target_trader_address == CORRECT_ADDRESS:
                print(f"    ✅ CORRECT ADDRESS!")

print("\n" + "=" * 80)
print("Fix complete! The bot should now detect 25usdc positions.")
print("It will check for new positions every 5 minutes.")
print("=" * 80)
