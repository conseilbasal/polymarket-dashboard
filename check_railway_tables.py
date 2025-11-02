"""
Check Railway database tables structure and data
"""

import os
from sqlalchemy import create_engine, text, inspect
from datetime import datetime

# Railway database URL
DATABASE_URL = "postgresql://postgres:osDFUPPrdSKBBGfpAEldJCSqXZJvmqRC@centerbeam.proxy.rlwy.net:58371/railway"

print("=" * 80)
print("Checking Railway database tables")
print("=" * 80)

engine = create_engine(DATABASE_URL)

# List all tables
print("\n1. All tables in database:")
inspector = inspect(engine)
tables = inspector.get_table_names()
for table in tables:
    print(f"  - {table}")

# Check positions_history structure
print("\n2. positions_history table structure:")
with engine.connect() as conn:
    query = text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'positions_history'
        ORDER BY ordinal_position
    """)
    result = conn.execute(query)
    columns = result.fetchall()
    for col in columns:
        print(f"  - {col.column_name}: {col.data_type}")

# Check most recent data in positions_history (any user)
print("\n3. Most recent positions in positions_history (any user):")
with engine.connect() as conn:
    query = text("""
        SELECT user, market, side, size, updated_at
        FROM positions_history
        ORDER BY updated_at DESC
        LIMIT 5
    """)
    result = conn.execute(query)
    rows = result.fetchall()
    if rows:
        for i, row in enumerate(rows):
            print(f"\n  Position #{i+1}:")
            print(f"    User: {row.user}")
            print(f"    Market: {row.market[:50]}...")
            print(f"    Side: {row.side}")
            print(f"    Size: {row.size}")
            print(f"    Updated: {row.updated_at}")
    else:
        print("  NO POSITIONS AT ALL!")

# Check position_snapshots structure (if it exists)
if 'position_snapshots' in tables:
    print("\n4. position_snapshots table structure:")
    with engine.connect() as conn:
        query = text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'position_snapshots'
            ORDER BY ordinal_position
        """)
        result = conn.execute(query)
        columns = result.fetchall()
        for col in columns:
            print(f"  - {col.column_name}: {col.data_type}")

    # Check data in position_snapshots
    print("\n5. Data in position_snapshots:")
    with engine.connect() as conn:
        query = text("""
            SELECT COUNT(*) as total
            FROM position_snapshots
        """)
        result = conn.execute(query)
        count = result.fetchone().total
        print(f"  Total snapshots: {count}")

# Check capital_history
print("\n6. Most recent capital_history entries:")
with engine.connect() as conn:
    query = text("""
        SELECT user, total_capital, positions_count, timestamp
        FROM capital_history
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    result = conn.execute(query)
    rows = result.fetchall()
    if rows:
        for i, row in enumerate(rows):
            print(f"\n  #{i+1}: {row.user}")
            print(f"    Capital: ${row.total_capital:.2f}")
            print(f"    Positions: {row.positions_count}")
            print(f"    Time: {row.timestamp}")
    else:
        print("  NO CAPITAL HISTORY!")

print("\n" + "=" * 80)
print("Check complete!")
print("=" * 80)
