-- Table pour stocker les positions en attente d'accumulation
-- Utilisée quand une position copiée est trop petite pour être placée immédiatement

CREATE TABLE IF NOT EXISTS pending_accumulation (
    id SERIAL PRIMARY KEY,
    user_wallet_address VARCHAR(42) NOT NULL,
    target_trader_address VARCHAR(100) NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    outcome VARCHAR(10) NOT NULL,
    accumulated_size FLOAT NOT NULL DEFAULT 0,
    accumulated_value_usd FLOAT NOT NULL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Une seule entrée par combinaison user/trader/market/outcome
    UNIQUE(user_wallet_address, target_trader_address, market_id, outcome)
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_pending_accumulation_lookup
ON pending_accumulation(user_wallet_address, target_trader_address, market_id, outcome);

-- Verification
SELECT 'pending_accumulation' as table_name, COUNT(*) as row_count FROM pending_accumulation;
