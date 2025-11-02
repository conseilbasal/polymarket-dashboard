"""
Check what positions are actually in the Railway database for 25usdc
"""

import os
from sqlalchemy import create_engine, text
from datetime import datetime

# Railway database URL
DATABASE_URL = "postgresql://postgres:osDFUPPrdSKBBGfpAEldJCSqXZJvmqRC@centerbeam.proxy.rlwy.net:58371/railway"

print("=" * 80)
print("Checking Railway database for 25usdc positions")
print("=" * 80)

engine = create_engine(DATABASE_URL)

# Check positions_history table
print("\n1. Checking positions_history table...")
with engine.connect() as conn:
    query = text("""
        SELECT user, market, side, size, avg_price, pnl, updated_at
        FROM positions_history
        WHERE user = '25usdc'
        ORDER BY updated_at DESC
        LIMIT 10
    """)

    result = conn.execute(query)
    rows = result.fetchall()

    if rows:
        print(f"\nFound {len(rows)} recent positions for 25usdc:")
        for i, row in enumerate(rows):
            print(f"\n  Position #{i+1}:")
            print(f"    Market: {row.market}")
            print(f"    Side: {row.side}")
            print(f"    Size: {row.size} shares")
            print(f"    Avg Price: ${row.avg_price:.4f}")
            print(f"    PnL: ${row.pnl:.2f}")
            print(f"    Updated: {row.updated_at}")
    else:
        print("  No positions found for 25usdc!")

# Check position_snapshots table (for copy trading)
print("\n2. Checking position_snapshots table (copy trading)...")
with engine.connect() as conn:
    query = text("""
        SELECT trader_address, market_name, side, size, avg_price, snapshot_time
        FROM position_snapshots
        WHERE trader_address = '0x00ce0682efd980b2caa0e8d7f7e5290fe4f9df0f'
        ORDER BY snapshot_time DESC
        LIMIT 10
    """)

    result = conn.execute(query)
    rows = result.fetchall()

    if rows:
        print(f"\nFound {len(rows)} snapshots for 25usdc:")
        for i, row in enumerate(rows):
            print(f"\n  Snapshot #{i+1}:")
            print(f"    Market: {row.market_name}")
            print(f"    Side: {row.side}")
            print(f"    Size: {row.size} shares")
            print(f"    Avg Price: ${row.avg_price:.4f}")
            print(f"    Time: {row.snapshot_time}")
    else:
        print("  No snapshots found for 25usdc!")

# Check most recent snapshot time for any trader
print("\n3. Checking most recent snapshot time...")
with engine.connect() as conn:
    query = text("""
        SELECT MAX(snapshot_time) as last_snapshot
        FROM position_snapshots
    """)

    result = conn.execute(query)
    row = result.fetchone()

    if row and row.last_snapshot:
        print(f"\n  Last snapshot: {row.last_snapshot}")
        print(f"  Time since last snapshot: {datetime.now() - row.last_snapshot}")
    else:
        print("  No snapshots found at all!")

# Check capital_history for 25usdc
print("\n4. Checking capital_history for 25usdc...")
with engine.connect() as conn:
    query = text("""
        SELECT user, total_capital, exposure, pnl, positions_count, timestamp
        FROM capital_history
        WHERE user = '25usdc'
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    result = conn.execute(query)
    rows = result.fetchall()

    if rows:
        print(f"\nFound {len(rows)} capital snapshots for 25usdc:")
        for i, row in enumerate(rows):
            print(f"\n  Snapshot #{i+1}:")
            print(f"    Capital: ${row.total_capital:.2f}")
            print(f"    Exposure: ${row.exposure:.2f}")
            print(f"    PnL: ${row.pnl:.2f}")
            print(f"    Positions: {row.positions_count}")
            print(f"    Time: {row.timestamp}")
    else:
        print("  No capital history found for 25usdc!")

print("\n" + "=" * 80)
print("Database check complete!")
print("=" * 80)
