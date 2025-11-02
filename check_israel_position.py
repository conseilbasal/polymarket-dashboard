from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:osDFUPPrdSKBBGfpAEldJCSqXZJvmqRC@centerbeam.proxy.rlwy.net:58371/railway"
engine = create_engine(DATABASE_URL)

print("Searching for Israel/Gaza position in snapshots...")
with engine.connect() as conn:
    q = text("""
        SELECT market_name, side, size, avg_price, snapshot_time
        FROM position_snapshots
        WHERE LOWER(market_name) LIKE '%israel%' OR LOWER(market_name) LIKE '%gaza%'
        ORDER BY snapshot_time DESC
        LIMIT 5
    """)
    result = conn.execute(q)
    rows = result.fetchall()

    if rows:
        print(f"\nFound {len(rows)} snapshot(s) with Israel/Gaza:")
        for row in rows:
            print(f"\n  {row.snapshot_time}")
            print(f"    Market: {row.market_name}")
            print(f"    Side: {row.side}")
            print(f"    Size: {row.size} shares")
            print(f"    Avg Price: ${row.avg_price:.4f}")
    else:
        print("\nNO Israel/Gaza position found in snapshots!")
        print("This means 25usdc took this position AFTER the last snapshot.")
        print("The bot will detect it on the NEXT run (in ~2-3 minutes)")
