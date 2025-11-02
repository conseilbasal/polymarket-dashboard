from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:osDFUPPrdSKBBGfpAEldJCSqXZJvmqRC@centerbeam.proxy.rlwy.net:58371/railway"
CORRECT_ADDRESS = "0x75e765216a57942d738d880ffcda854d9f869080"

engine = create_engine(DATABASE_URL)

# Update
with engine.connect() as conn:
    query = text("UPDATE copy_trading_config SET target_trader_address = :addr WHERE target_trader_name = '25usdc'")
    result = conn.execute(query, {"addr": CORRECT_ADDRESS})
    conn.commit()
    print(f"Updated {result.rowcount} row(s)")

# Verify
with engine.connect() as conn:
    query = text("SELECT target_trader_address, target_trader_name, copy_percentage FROM copy_trading_config")
    result = conn.execute(query)
    for row in result:
        print(f"\nTrader: {row.target_trader_name}")
        print(f"Address: {row.target_trader_address}")
        print(f"Copy %: {row.copy_percentage}%")
