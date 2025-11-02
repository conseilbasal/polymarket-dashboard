"""
Fix the position_snapshots table schema to match what copy_trading_engine expects
"""

from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:osDFUPPrdSKBBGfpAEldJCSqXZJvmqRC@centerbeam.proxy.rlwy.net:58371/railway"

print("=" * 80)
print("Fixing position_snapshots table schema")
print("=" * 80)

engine = create_engine(DATABASE_URL)

# Drop existing table
print("\n1. Dropping existing position_snapshots table...")
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS position_snapshots"))
    conn.commit()
    print("   Table dropped")

# Create new table with correct schema
print("\n2. Creating position_snapshots with correct schema...")
with engine.connect() as conn:
    # Schema that matches copy_trading_engine.py expectations
    create_table_sql = text("""
        CREATE TABLE position_snapshots (
            id SERIAL PRIMARY KEY,
            trader_address VARCHAR(100) NOT NULL,
            market_id VARCHAR(100) NOT NULL,
            market_name TEXT,
            token_id VARCHAR(100) NOT NULL,
            side VARCHAR(10) NOT NULL,
            size FLOAT NOT NULL,
            avg_price FLOAT NOT NULL,
            snapshot_time TIMESTAMP DEFAULT NOW(),
            UNIQUE(trader_address, market_id, token_id, snapshot_time)
        )
    """)

    conn.execute(create_table_sql)
    conn.commit()
    print("   Table created with correct schema")

# Verify schema
print("\n3. Verifying new schema...")
with engine.connect() as conn:
    query = text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'position_snapshots'
        ORDER BY ordinal_position
    """)
    result = conn.execute(query)
    columns = result.fetchall()

    print("\n   Columns in position_snapshots:")
    for col in columns:
        print(f"     - {col.column_name}: {col.data_type}")

print("\n" + "=" * 80)
print("Table fixed! Copy trading engine should work now.")
print("Next scheduler run will create snapshots and detect position changes.")
print("=" * 80)
