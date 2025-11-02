"""
Create Copy Trading tables in Railway PostgreSQL database
Run this script once to set up the database schema
"""

import os
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    print("Set it with: set DATABASE_URL=your_railway_postgres_url")
    exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

# SQL to create tables
CREATE_TABLES_SQL = """
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

-- Table 2: Position Snapshots (for tracking target trader positions)
CREATE TABLE IF NOT EXISTS position_snapshots (
    id SERIAL PRIMARY KEY,
    target_trader_address VARCHAR(100) NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    outcome VARCHAR(10) NOT NULL,
    size FLOAT NOT NULL,
    avg_entry_price FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_trader_market (target_trader_address, market_id, timestamp)
);

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
    error_message TEXT,
    INDEX idx_user_status (user_wallet_address, status),
    INDEX idx_order_id (order_id)
);

-- Table 4: Executed Copy Trades (history)
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
    pnl FLOAT,
    INDEX idx_user_trades (user_wallet_address, executed_at),
    INDEX idx_target_trades (target_trader_address, executed_at)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_config_user ON copy_trading_config(user_wallet_address);
CREATE INDEX IF NOT EXISTS idx_config_enabled ON copy_trading_config(enabled);
CREATE INDEX IF NOT EXISTS idx_snapshots_trader_time ON position_snapshots(target_trader_address, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pending_status_time ON pending_copy_orders(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_executed_user_time ON executed_copy_trades(user_wallet_address, executed_at DESC);
"""

print("Creating Copy Trading tables in Railway PostgreSQL...")
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")
print()

try:
    with engine.connect() as conn:
        # Execute each statement
        for statement in CREATE_TABLES_SQL.strip().split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                conn.execute(text(statement))
                conn.commit()

    print("✓ copy_trading_config table created")
    print("✓ position_snapshots table created")
    print("✓ pending_copy_orders table created")
    print("✓ executed_copy_trades table created")
    print("✓ All indexes created")
    print()
    print("SUCCESS! Copy Trading database schema is ready.")
    print()
    print("You can now:")
    print("1. Enable copy trading via API: POST /api/copy-trading/enable")
    print("2. View status: GET /api/copy-trading/status")
    print("3. View history: GET /api/copy-trading/history")

except Exception as e:
    print(f"ERROR: Failed to create tables")
    print(f"Details: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
