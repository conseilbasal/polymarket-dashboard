-- Migration: Copy Trading Schema
-- Description: Tables for automatic copy trading functionality
-- Date: 2025-01-31

-- Table 1: Copy Trading Configuration
-- Stores which traders each user wants to copy and with what percentage
CREATE TABLE IF NOT EXISTS copy_trading_config (
    id SERIAL PRIMARY KEY,
    user_wallet_address VARCHAR(42) NOT NULL,
    target_trader_address VARCHAR(42) NOT NULL,
    target_trader_name VARCHAR(255),
    copy_percentage DECIMAL(5,2) NOT NULL CHECK (copy_percentage > 0 AND copy_percentage <= 100),
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_wallet_address, target_trader_address)
);

CREATE INDEX IF NOT EXISTS idx_copy_config_user ON copy_trading_config(user_wallet_address);
CREATE INDEX IF NOT EXISTS idx_copy_config_enabled ON copy_trading_config(enabled) WHERE enabled = true;

-- Table 2: Position Snapshots
-- Historical snapshots of trader positions to detect changes
CREATE TABLE IF NOT EXISTS position_snapshots (
    id SERIAL PRIMARY KEY,
    trader_address VARCHAR(42) NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    market_name VARCHAR(500),
    token_id VARCHAR(100) NOT NULL,
    side VARCHAR(3) NOT NULL CHECK (side IN ('YES', 'NO')),
    size DECIMAL(18,6) NOT NULL,
    avg_price DECIMAL(10,8) NOT NULL,
    snapshot_time TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_trader_time ON position_snapshots(trader_address, snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_market ON position_snapshots(market_id, snapshot_time DESC);

-- Table 3: Pending Copy Orders
-- Orders that have been placed but not yet fully executed
CREATE TABLE IF NOT EXISTS pending_copy_orders (
    id SERIAL PRIMARY KEY,
    user_wallet_address VARCHAR(42) NOT NULL,
    target_trader_address VARCHAR(42) NOT NULL,
    target_trader_name VARCHAR(255),
    market_id VARCHAR(100) NOT NULL,
    market_name VARCHAR(500),
    token_id VARCHAR(100) NOT NULL,
    side VARCHAR(3) NOT NULL CHECK (side IN ('YES', 'NO')),
    order_side VARCHAR(4) NOT NULL CHECK (order_side IN ('BUY', 'SELL')),
    target_size DECIMAL(18,6) NOT NULL,
    target_price DECIMAL(10,8) NOT NULL,
    initial_price DECIMAL(10,8) NOT NULL,
    current_price DECIMAL(10,8) NOT NULL,
    clob_order_id VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'partial', 'filled', 'cancelled', 'failed')),
    filled_size DECIMAL(18,6) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    last_price_adjustment TIMESTAMP,
    price_adjustment_count INT DEFAULT 0,
    failure_reason TEXT,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_pending_orders_user ON pending_copy_orders(user_wallet_address);
CREATE INDEX IF NOT EXISTS idx_pending_orders_status ON pending_copy_orders(status) WHERE status IN ('pending', 'partial');
CREATE INDEX IF NOT EXISTS idx_pending_orders_clob ON pending_copy_orders(clob_order_id) WHERE clob_order_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_pending_orders_time ON pending_copy_orders(created_at DESC);

-- Table 4: Executed Copy Trades
-- Historical record of all successfully executed copy trades
CREATE TABLE IF NOT EXISTS executed_copy_trades (
    id SERIAL PRIMARY KEY,
    user_wallet_address VARCHAR(42) NOT NULL,
    target_trader_address VARCHAR(42) NOT NULL,
    target_trader_name VARCHAR(255),
    market_id VARCHAR(100) NOT NULL,
    market_name VARCHAR(500),
    token_id VARCHAR(100) NOT NULL,
    side VARCHAR(3) NOT NULL CHECK (side IN ('YES', 'NO')),
    order_side VARCHAR(4) NOT NULL CHECK (order_side IN ('BUY', 'SELL')),
    size DECIMAL(18,6) NOT NULL,
    price DECIMAL(10,8) NOT NULL,
    target_price DECIMAL(10,8) NOT NULL,
    slippage DECIMAL(10,8),
    slippage_percentage DECIMAL(5,2),
    tx_hash VARCHAR(100),
    clob_order_id VARCHAR(100),
    profit_loss DECIMAL(18,6),
    executed_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_executed_trades_user ON executed_copy_trades(user_wallet_address);
CREATE INDEX IF NOT EXISTS idx_executed_trades_trader ON executed_copy_trades(target_trader_address);
CREATE INDEX IF NOT EXISTS idx_executed_trades_time ON executed_copy_trades(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_executed_trades_market ON executed_copy_trades(market_id);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on copy_trading_config
DROP TRIGGER IF EXISTS update_copy_config_updated_at ON copy_trading_config;
CREATE TRIGGER update_copy_config_updated_at
    BEFORE UPDATE ON copy_trading_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update last_updated on pending_copy_orders
DROP TRIGGER IF EXISTS update_pending_orders_updated_at ON pending_copy_orders;
CREATE TRIGGER update_pending_orders_updated_at
    BEFORE UPDATE ON pending_copy_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE copy_trading_config IS 'Configuration for which traders each user wants to copy automatically';
COMMENT ON TABLE position_snapshots IS 'Historical snapshots of trader positions for detecting changes';
COMMENT ON TABLE pending_copy_orders IS 'Orders that have been placed but not yet fully executed';
COMMENT ON TABLE executed_copy_trades IS 'Historical record of all successfully executed copy trades';

-- Grant permissions (if using specific database user)
-- GRANT ALL PRIVILEGES ON TABLE copy_trading_config TO your_db_user;
-- GRANT ALL PRIVILEGES ON TABLE position_snapshots TO your_db_user;
-- GRANT ALL PRIVILEGES ON TABLE pending_copy_orders TO your_db_user;
-- GRANT ALL PRIVILEGES ON TABLE executed_copy_trades TO your_db_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_db_user;
