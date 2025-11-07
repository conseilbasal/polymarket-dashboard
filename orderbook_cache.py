"""
Orderbook Cache Manager
Fetches and caches bid/ask/spread data for markets using py-clob-client
"""

import logging
import time
import os
from typing import Dict, List, Optional
from sqlalchemy import text
from database import engine
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class OrderbookCache:
    """Manages orderbook data caching for markets using py-clob-client"""

    def __init__(self):
        # Initialize the CLOB client (read-only, no auth needed)
        self.client = ClobClient("https://clob.polymarket.com")
        self.markets_cache = None
        self.last_cache_update = 0
        self.cache_ttl = 300  # Cache markets for 5 minutes

    def _get_all_markets(self) -> List[Dict]:
        """Get all markets from Polymarket, with caching"""
        current_time = time.time()

        # Return cached markets if still valid
        if self.markets_cache and (current_time - self.last_cache_update) < self.cache_ttl:
            return self.markets_cache

        try:
            logger.info("Fetching all markets from Polymarket...")
            markets_data = self.client.get_simplified_markets()
            # Extract the 'data' field which contains the list of markets
            self.markets_cache = markets_data.get('data', [])
            self.last_cache_update = current_time
            logger.info(f"Loaded {len(self.markets_cache)} markets into cache")
            return self.markets_cache
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return self.markets_cache if self.markets_cache else []

    def get_token_id_from_market(self, market_name: str, side: str) -> Optional[str]:
        """
        Get token_id for a market from Polymarket /positions API

        Args:
            market_name: Market question text
            side: 'Yes' or 'No'

        Returns:
            token_id or None if not found
        """
        try:
            import requests
            import json
            from pathlib import Path

            # Load traders config to get wallet addresses
            config_path = Path(__file__).parent / "config" / "traders.json"
            if not config_path.exists():
                logger.warning("traders.json not found")
                return None

            with open(config_path) as f:
                traders_config = json.load(f)["TRADERS"]

            # Try each trader's positions to find the market
            for trader in traders_config:
                wallet_address = trader['address']

                # Fetch positions for this wallet
                url = f"https://data-api.polymarket.com/positions?user={wallet_address}&limit=500"
                response = requests.get(url, timeout=10)

                if response.status_code != 200:
                    continue

                positions = response.json()

                # Search for matching market name
                market_name_lower = market_name.lower().strip()
                for position in positions:
                    position_title = position.get('title', '').lower().strip()
                    position_outcome = position.get('outcome', '').lower().strip()

                    if position_title == market_name_lower and position_outcome == side.lower():
                        token_id = position.get('asset')
                        if token_id:
                            logger.info(f"Found token_id {token_id} for {market_name} ({side})")
                            return token_id

            logger.warning(f"No token_id found for market: {market_name} ({side})")
            return None

        except Exception as e:
            logger.error(f"Error fetching token_id for {market_name}: {e}")
            return None

    def fetch_orderbook_data(self, token_id: str) -> Optional[Dict]:
        """
        Fetch orderbook data from CLOB using py-clob-client

        Args:
            token_id: Token ID

        Returns:
            Dict with bid/ask/spread data or None
        """
        try:
            # Use py-clob-client to get orderbook
            orderbook = self.client.get_order_book(token_id)

            if not orderbook:
                return None

            # OrderBookSummary object has attributes, not dict keys
            bids = getattr(orderbook, 'bids', [])
            asks = getattr(orderbook, 'asks', [])

            if not bids or not asks:
                logger.warning(f"No bids or asks for token {token_id}")
                return {
                    'best_bid': 0,
                    'best_ask': 0,
                    'mid_price': 0,
                    'spread': 0,
                    'spread_percentage': 0
                }

            # Access bid/ask prices from the order objects
            best_bid = float(bids[0].price) if hasattr(bids[0], 'price') else float(bids[0]['price'])
            best_ask = float(asks[0].price) if hasattr(asks[0], 'price') else float(asks[0]['price'])
            mid_price = (best_bid + best_ask) / 2
            spread = best_ask - best_bid
            spread_pct = (spread / mid_price) * 100 if mid_price > 0 else 0

            return {
                'best_bid': best_bid,
                'best_ask': best_ask,
                'mid_price': mid_price,
                'spread': spread,
                'spread_percentage': spread_pct
            }

        except Exception as e:
            logger.error(f"Error fetching orderbook for token {token_id}: {e}")
            return None

    def update_market_orderbook(self, market_name: str, side: str):
        """
        Update orderbook data for a specific market

        Args:
            market_name: Market name
            side: 'Yes' or 'No'
        """
        try:
            # Get token_id
            token_id = self.get_token_id_from_market(market_name, side)

            if not token_id:
                logger.warning(f"Could not get token_id for {market_name} ({side})")
                return

            # Fetch orderbook data
            orderbook = self.fetch_orderbook_data(token_id)

            if not orderbook:
                logger.warning(f"Could not fetch orderbook for {market_name} ({side})")
                return

            # Save to database
            with engine.connect() as conn:
                query = text("""
                    INSERT INTO market_orderbook
                    (market_name, side, token_id, best_bid, best_ask, mid_price, spread, spread_percentage, last_updated)
                    VALUES
                    (:market_name, :side, :token_id, :best_bid, :best_ask, :mid_price, :spread, :spread_pct, CURRENT_TIMESTAMP)
                    ON CONFLICT(market_name, side)
                    DO UPDATE SET
                        token_id = :token_id,
                        best_bid = :best_bid,
                        best_ask = :best_ask,
                        mid_price = :mid_price,
                        spread = :spread,
                        spread_percentage = :spread_pct,
                        last_updated = CURRENT_TIMESTAMP
                """)

                conn.execute(query, {
                    'market_name': market_name,
                    'side': side,
                    'token_id': token_id,
                    'best_bid': orderbook['best_bid'],
                    'best_ask': orderbook['best_ask'],
                    'mid_price': orderbook['mid_price'],
                    'spread': orderbook['spread'],
                    'spread_pct': orderbook['spread_percentage']
                })
                conn.commit()

            logger.info(f"Updated orderbook for {market_name} ({side}): bid={orderbook['best_bid']:.3f}, ask={orderbook['best_ask']:.3f}")

        except Exception as e:
            logger.error(f"Error updating orderbook for {market_name}: {e}")

    def refresh_all_active_markets(self):
        """Refresh orderbook data for all active markets from latest CSV snapshot"""
        try:
            import pandas as pd
            from pathlib import Path

            # Get latest snapshot CSV (same logic as API)
            snapshots_dir = Path(__file__).parent / "data" / "snapshots"
            snapshots = sorted(snapshots_dir.glob("positions_*.csv"))

            if not snapshots:
                logger.warning("No snapshots found, cannot refresh orderbook")
                return

            # Read latest snapshot
            latest_snapshot = snapshots[-1]
            df = pd.read_csv(latest_snapshot)

            # Get unique market/side combinations
            markets = df[['market', 'side']].drop_duplicates()

            logger.info(f"Refreshing orderbook data for {len(markets)} markets from {latest_snapshot.name}...")

            success_count = 0
            for _, row in markets.iterrows():
                market_name = row['market']
                side = row['side']

                try:
                    self.update_market_orderbook(market_name, side)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to update {market_name} ({side}): {e}")

                # Small delay to avoid rate limiting
                time.sleep(0.3)

            logger.info(f"Finished refreshing {success_count}/{len(markets)} markets successfully")

        except Exception as e:
            logger.error(f"Error refreshing all markets: {e}")

    def get_orderbook_for_market(self, market_name: str, side: str) -> Optional[Dict]:
        """
        Get cached orderbook data for a market

        Args:
            market_name: Market name
            side: 'Yes' or 'No'

        Returns:
            Dict with orderbook data or None
        """
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT best_bid, best_ask, mid_price, spread, spread_percentage, last_updated
                    FROM market_orderbook
                    WHERE market_name = :market_name AND side = :side
                """)

                result = conn.execute(query, {
                    'market_name': market_name,
                    'side': side
                })

                row = result.fetchone()

                if row:
                    return {
                        'best_bid': float(row[0]) if row[0] else 0,
                        'best_ask': float(row[1]) if row[1] else 0,
                        'mid_price': float(row[2]) if row[2] else 0,
                        'spread': float(row[3]) if row[3] else 0,
                        'spread_percentage': float(row[4]) if row[4] else 0,
                        'last_updated': row[5]
                    }

                return None

        except Exception as e:
            logger.error(f"Error getting orderbook for {market_name}: {e}")
            return None

# Global instance
orderbook_cache = OrderbookCache()
