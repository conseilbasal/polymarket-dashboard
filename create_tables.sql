-- Create Copy Trading tables for PostgreSQL on Railway
-- Run this directly in Railway's PostgreSQL database

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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_snapshots_trader_time ON position_snapshots(target_trader_address, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pending_status_time ON pending_copy_orders(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_executed_user_time ON executed_copy_trades(user_wallet_address, executed_at DESC);

-- Verify tables were created
SELECT 'copy_trading_config' as table_name, COUNT(*) as row_count FROM copy_trading_config
UNION ALL
SELECT 'position_snapshots', COUNT(*) FROM position_snapshots
UNION ALL
SELECT 'pending_copy_orders', COUNT(*) FROM pending_copy_orders
UNION ALL
SELECT 'executed_copy_trades', COUNT(*) FROM executed_copy_trades;
