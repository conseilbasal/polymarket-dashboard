"""
Initialize Copy Trading database tables
This runs automatically on Railway startup via api_server.py
"""

from sqlalchemy import text
from database import engine

def init_copy_trading_tables():
    """Create Copy Trading tables if they don't exist"""

    print("[DB INIT] Checking Copy Trading tables...")

    # SQL to create tables (PostgreSQL and SQLite compatible)
    CREATE_TABLES_SQL = """
    -- Table 1: Copy Trading Configuration
    CREATE TABLE IF NOT EXISTS copy_trading_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_wallet_address VARCHAR(42) NOT NULL,
        target_trader_address VARCHAR(100) NOT NULL,
        target_trader_name VARCHAR(100),
        copy_percentage FLOAT NOT NULL,
        enabled BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_wallet_address, target_trader_address)
    );

    -- Table 2: Position Snapshots
    CREATE TABLE IF NOT EXISTS position_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_trader_address VARCHAR(100) NOT NULL,
        market_id VARCHAR(100) NOT NULL,
        outcome VARCHAR(10) NOT NULL,
        size FLOAT NOT NULL,
        avg_entry_price FLOAT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Table 3: Pending Copy Orders
    CREATE TABLE IF NOT EXISTS pending_copy_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_wallet_address VARCHAR(42) NOT NULL,
        target_trader_address VARCHAR(100) NOT NULL,
        market_id VARCHAR(100) NOT NULL,
        outcome VARCHAR(10) NOT NULL,
        size FLOAT NOT NULL,
        price FLOAT NOT NULL,
        side VARCHAR(10) NOT NULL,
        order_id VARCHAR(100) UNIQUE,
        status VARCHAR(20) DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        filled_at TIMESTAMP,
        error_message TEXT
    );

    -- Table 4: Executed Copy Trades
    CREATE TABLE IF NOT EXISTS executed_copy_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_wallet_address VARCHAR(42) NOT NULL,
        target_trader_address VARCHAR(100) NOT NULL,
        target_trader_name VARCHAR(100),
        market_id VARCHAR(100) NOT NULL,
        market_title TEXT,
        outcome VARCHAR(10) NOT NULL,
        side VARCHAR(10) NOT NULL,
        size FLOAT NOT NULL,
        price FLOAT NOT NULL,
        copy_percentage FLOAT NOT NULL,
        order_id VARCHAR(100),
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        pnl FLOAT
    );
    """

    # PostgreSQL version (with SERIAL and better constraints)
    CREATE_TABLES_POSTGRES = """
    -- Table 1: Copy Trading Configuration
    CREATE TABLE IF NOT EXISTS copy_trading_config (
        id SERIAL PRIMARY KEY,
        user_wallet_address VARCHAR(42) NOT NULL,
        target_trader_address VARCHAR(100) NOT NULL,
        target_trader_name VARCHAR(100),
        copy_percentage FLOAT NOT NULL CHECK (copy_percentage >= 0.1 AND copy_percentage <= 100),
        enabled BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(user_wallet_address, target_trader_address)
    );

    -- Table 2: Position Snapshots
    CREATE TABLE IF NOT EXISTS position_snapshots (
        id SERIAL PRIMARY KEY,
        target_trader_address VARCHAR(100) NOT NULL,
        market_id VARCHAR(100) NOT NULL,
        outcome VARCHAR(10) NOT NULL,
        size FLOAT NOT NULL,
        avg_entry_price FLOAT,
        timestamp TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_snapshots_trader_time ON position_snapshots(target_trader_address, timestamp DESC);

    -- Table 3: Pending Copy Orders
    CREATE TABLE IF NOT EXISTS pending_copy_orders (
        id SERIAL PRIMARY KEY,
        user_wallet_address VARCHAR(42) NOT NULL,
        target_trader_address VARCHAR(100) NOT NULL,
        market_id VARCHAR(100) NOT NULL,
        outcome VARCHAR(10) NOT NULL,
        size FLOAT NOT NULL,
        price FLOAT NOT NULL,
        side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
        order_id VARCHAR(100) UNIQUE,
        status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'FILLED', 'CANCELLED', 'FAILED')),
        created_at TIMESTAMP DEFAULT NOW(),
        filled_at TIMESTAMP,
        error_message TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_pending_status_time ON pending_copy_orders(status, created_at DESC);

    -- Table 4: Executed Copy Trades
    CREATE TABLE IF NOT EXISTS executed_copy_trades (
        id SERIAL PRIMARY KEY,
        user_wallet_address VARCHAR(42) NOT NULL,
        target_trader_address VARCHAR(100) NOT NULL,
        target_trader_name VARCHAR(100),
        market_id VARCHAR(100) NOT NULL,
        market_title TEXT,
        outcome VARCHAR(10) NOT NULL,
        side VARCHAR(10) NOT NULL,
        size FLOAT NOT NULL,
        price FLOAT NOT NULL,
        copy_percentage FLOAT NOT NULL,
        order_id VARCHAR(100),
        executed_at TIMESTAMP DEFAULT NOW(),
        pnl FLOAT
    );
    CREATE INDEX IF NOT EXISTS idx_executed_user_time ON executed_copy_trades(user_wallet_address, executed_at DESC);
    """

    try:
        is_postgres = str(engine.url).startswith('postgresql')
        sql_to_use = CREATE_TABLES_POSTGRES if is_postgres else CREATE_TABLES_SQL

        with engine.connect() as conn:
            # Execute all statements
            for statement in sql_to_use.strip().split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    conn.execute(text(statement))
                    conn.commit()

        db_type = "PostgreSQL" if is_postgres else "SQLite"
        print(f"[DB INIT] ✓ Copy Trading tables created/verified in {db_type}")
        print("[DB INIT] ✓ copy_trading_config")
        print("[DB INIT] ✓ position_snapshots")
        print("[DB INIT] ✓ pending_copy_orders")
        print("[DB INIT] ✓ executed_copy_trades")

        return True

    except Exception as e:
        print(f"[DB INIT ERROR] Failed to create Copy Trading tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Can be run standalone for testing
    success = init_copy_trading_tables()
    if success:
        print("\nSUCCESS! Copy Trading database is ready.")
    else:
        print("\nFAILED! Check errors above.")
