# coding: utf-8
"""
Script to create Copy Trading tables directly on Railway PostgreSQL
Run this once to create the missing tables
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Railway PostgreSQL Public URL
DATABASE_URL = "postgresql://postgres:osDFUPPrdSKBBGfpAEldJCSqXZJvmqRC@centerbeam.proxy.rlwy.net:58371/railway"

print("Connexion a la base de donnees...")

try:
    # Connect to Railway PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("[OK] Connecte a PostgreSQL")
    print()

    # Create tables
    tables_sql = [
        # Table 1
        """
        CREATE TABLE IF NOT EXISTS copy_trading_config (
            id SERIAL PRIMARY KEY,
            user_wallet_address VARCHAR(42) NOT NULL,
            target_trader_address VARCHAR(100) NOT NULL,
            target_trader_name VARCHAR(100),
            copy_percentage FLOAT NOT NULL,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_wallet_address, target_trader_address)
        )
        """,

        # Table 2
        """
        CREATE TABLE IF NOT EXISTS position_snapshots (
            id SERIAL PRIMARY KEY,
            target_trader_address VARCHAR(100) NOT NULL,
            market_id VARCHAR(100) NOT NULL,
            outcome VARCHAR(10) NOT NULL,
            size FLOAT NOT NULL,
            avg_entry_price FLOAT,
            timestamp TIMESTAMP DEFAULT NOW()
        )
        """,

        # Table 3
        """
        CREATE TABLE IF NOT EXISTS pending_copy_orders (
            id SERIAL PRIMARY KEY,
            user_wallet_address VARCHAR(42) NOT NULL,
            target_trader_address VARCHAR(100) NOT NULL,
            market_id VARCHAR(100) NOT NULL,
            outcome VARCHAR(10) NOT NULL,
            size FLOAT NOT NULL,
            price FLOAT NOT NULL,
            side VARCHAR(10) NOT NULL,
            order_id VARCHAR(100) UNIQUE,
            status VARCHAR(20) DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT NOW(),
            filled_at TIMESTAMP,
            error_message TEXT
        )
        """,

        # Table 4
        """
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
        )
        """
    ]

    table_names = ['copy_trading_config', 'position_snapshots', 'pending_copy_orders', 'executed_copy_trades']

    for i, sql in enumerate(tables_sql):
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"[OK] Table creee: {table_names[i]}")
        except Exception as e:
            print(f"[ERROR] Erreur pour {table_names[i]}: {e}")

    print()
    print("=" * 60)
    print("Verification des tables creees...")
    print("=" * 60)

    # Verify tables exist
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('copy_trading_config', 'position_snapshots', 'pending_copy_orders', 'executed_copy_trades')
        ORDER BY table_name
    """)

    tables = cursor.fetchall()
    print(f"\nTables trouvees: {len(tables)}/4")
    for table in tables:
        print(f"  [OK] {table[0]}")

    if len(tables) == 4:
        print("\n[SUCCESS] Toutes les tables Copy Trading sont creees!")
    else:
        print(f"\n[WARNING] Seulement {len(tables)}/4 tables creees")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"[ERROR] Erreur de connexion: {e}")
    print()
    print("Pour obtenir l'URL publique PostgreSQL:")
    print("1. Allez sur Railway -> service Postgres")
    print("2. Onglet 'Connect'")
    print("3. Copiez 'Postgres Connection URL' (commence par postgresql://)")
