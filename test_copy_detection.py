"""
Test copy trading detection for the new Monad position
"""

import requests
from datetime import datetime

# Correct 25usdc address
TRADER_ADDRESS = "0x75e765216a57942d738d880ffcda854d9f869080"

print("=" * 80)
print("Testing Copy Trading Detection")
print(f"Time: {datetime.now()}")
print("=" * 80)

# Fetch current positions
url = f"https://data-api.polymarket.com/positions?user={TRADER_ADDRESS}"
print(f"\nFetching positions from API...")

response = requests.get(url, timeout=10)

if response.status_code == 200:
    positions = response.json()
    print(f"Total positions: {len(positions)}")

    # Look for the Monad position
    print("\nSearching for Monad airdrop position...")

    monad_found = False
    for pos in positions:
        title = pos.get('title', '').lower()
        market_slug = pos.get('market_slug', '').lower()

        if 'monad' in title or 'monad' in market_slug:
            monad_found = True
            print(f"\n✓ FOUND: Monad position")
            print(f"  Market: {pos.get('title', 'N/A')}")
            print(f"  Market ID: {pos.get('market', 'N/A')}")
            print(f"  Token ID: {pos.get('asset_id', 'N/A')}")
            print(f"  Side: {pos.get('outcome', 'N/A')}")
            print(f"  Size: {pos.get('size', 0)} shares")
            print(f"  Avg Price: ${pos.get('avgPrice', pos.get('avg_price', 0)):.4f}")
            print(f"  Value: ${pos.get('value', 0):.2f}")

            # Calculate what the bot should copy (5%)
            size = float(pos.get('size', 0))
            copy_size = size * 0.05
            print(f"\n  → Bot should copy: {copy_size:.2f} shares (5% of {size})")

    if not monad_found:
        print("\n✗ Monad position NOT found in API response")
        print("\nShowing all positions with 'November' in title:")
        for pos in positions:
            title = pos.get('title', '').lower()
            if 'november' in title:
                print(f"\n  - {pos.get('title', 'N/A')}")
                print(f"    Side: {pos.get('outcome', 'N/A')}")
                print(f"    Size: {pos.get('size', 0)} shares")

    print("\n" + "=" * 80)

    # Check database to see if Railway has already saved a snapshot
    print("\nChecking Railway database for snapshots...")

    from sqlalchemy import create_engine, text
    DATABASE_URL = "postgresql://postgres:osDFUPPrdSKBBGfpAEldJCSqXZJvmqRC@centerbeam.proxy.rlwy.net:58371/railway"
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        query = text("""
            SELECT COUNT(*) as count
            FROM position_snapshots
            WHERE target_trader_address = :trader_address
        """)
        result = conn.execute(query, {"trader_address": TRADER_ADDRESS})
        count = result.fetchone().count

        print(f"  Snapshots in DB: {count}")

        if count == 0:
            print("  → Bot has NOT created any snapshots yet")
            print("  → This means copy trading engine is NOT running on Railway")
        else:
            print(f"  → Bot has {count} snapshots")

            # Get latest snapshot
            query2 = text("""
                SELECT market_id, outcome, size, timestamp
                FROM position_snapshots
                WHERE target_trader_address = :trader_address
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            result2 = conn.execute(query2, {"trader_address": TRADER_ADDRESS})
            rows = result2.fetchall()

            print("\n  Latest snapshots:")
            for row in rows:
                print(f"    - {row.market_id[:20]}... {row.outcome}: {row.size} shares @ {row.timestamp}")

else:
    print(f"ERROR: HTTP {response.status_code}")
    print(response.text)

print("=" * 80)
