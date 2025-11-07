"""
Create market orderbook cache table for bid/ask/spread data
"""

from database import engine
from sqlalchemy import text

def create_orderbook_table():
    """Create market_orderbook table for caching bid/ask data"""

    create_table_query = text("""
    CREATE TABLE IF NOT EXISTS market_orderbook (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        market_name TEXT NOT NULL,
        side TEXT NOT NULL,
        token_id TEXT NOT NULL,
        best_bid REAL,
        best_ask REAL,
        mid_price REAL,
        spread REAL,
        spread_percentage REAL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(market_name, side)
    )
    """)

    with engine.connect() as conn:
        conn.execute(create_table_query)
        conn.commit()
        print("Created market_orderbook table")

if __name__ == "__main__":
    create_orderbook_table()
