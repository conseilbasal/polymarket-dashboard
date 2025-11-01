"""
Copy Trading Engine - Main orchestrator
Monitors trader positions, detects changes, executes copy trades
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import requests
from sqlalchemy import create_engine, text
from clob_client import PolymarketCLOBClient
from smart_pricing import SmartPricingEngine

logger = logging.getLogger(__name__)

class CopyTradingEngine:
    """
    Main copy trading engine that:
    1. Monitors positions of traders being copied
    2. Detects changes (new positions, size changes, closures)
    3. Executes proportional copy trades
    4. Manages pending orders (price adjustments, cancellations)
    """

    def __init__(self):
        """Initialize the copy trading engine"""

        # Database connection
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not set")

        self.engine = create_engine(database_url)

        # CLOB client for order execution
        self.clob_client = PolymarketCLOBClient()

        # Smart pricing algorithm
        self.pricing_engine = SmartPricingEngine()

        # Minimum trade size (in dollars)
        self.MIN_TRADE_SIZE = 1.0

        logger.info("✅ Copy Trading Engine initialized")

    async def monitor_positions(self):
        """
        Main monitoring loop - runs every 5 minutes
        Detects position changes for all traders being copied
        """

        logger.info("🔍 Starting position monitoring cycle...")

        try:
            # Get all active copy trading configs
            configs = self._get_active_configs()

            if not configs:
                logger.info("No active copy trading configs found")
                return

            logger.info(f"Monitoring {len(configs)} active copy trading config(s)")

            for config in configs:
                try:
                    await self._monitor_trader(config)
                except Exception as e:
                    logger.error(f"Error monitoring trader {config['target_trader_address']}: {e}")
                    continue

            logger.info("✅ Position monitoring cycle completed")

        except Exception as e:
            logger.error(f"Error in monitor_positions: {e}")

    async def _monitor_trader(self, config: Dict):
        """
        Monitor a specific trader for position changes

        Args:
            config: Copy trading configuration dict
        """

        trader_address = config['target_trader_address']
        trader_name = config['target_trader_name']
        copy_percentage = float(config['copy_percentage'])

        logger.info(f"Monitoring {trader_name} ({trader_address[:8]}...) at {copy_percentage}%")

        # Fetch current positions from Polymarket
        current_positions = self._fetch_trader_positions(trader_address)

        # Get last snapshot from database
        last_snapshot = self._get_last_snapshot(trader_address)

        # Detect changes
        changes = self._detect_position_changes(last_snapshot, current_positions)

        if changes:
            logger.info(f"Detected {len(changes)} position change(s) for {trader_name}")

            for change in changes:
                try:
                    await self._execute_copy_trade(config, change)
                except Exception as e:
                    logger.error(f"Failed to execute copy trade: {e}")

        # Save new snapshot
        self._save_snapshot(trader_address, current_positions)

    def _fetch_trader_positions(self, trader_address: str) -> Dict:
        """
        Fetch current positions for a trader from Polymarket API

        Returns:
            Dict[market_id_token_id, position_data]
        """

        try:
            # Use data-api to get positions
            url = f"https://data-api.polymarket.com/positions?user={trader_address}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch positions for {trader_address}: {response.status_code}")
                return {}

            positions_data = response.json()

            # Format as dict keyed by market_id + token_id
            positions = {}
            for pos in positions_data:
                market_id = pos.get('market')
                token_id = pos.get('asset_id')  # This is the token ID (YES or NO)

                if not market_id or not token_id:
                    continue

                key = f"{market_id}_{token_id}"

                positions[key] = {
                    'market_id': market_id,
                    'market_name': pos.get('market_slug', ''),
                    'token_id': token_id,
                    'side': pos.get('outcome', 'YES'),  # YES or NO
                    'size': float(pos.get('size', 0)),
                    'avg_price': float(pos.get('avg_price', 0)),
                    'value': float(pos.get('value', 0))
                }

            logger.info(f"Fetched {len(positions)} position(s) for {trader_address[:8]}...")
            return positions

        except Exception as e:
            logger.error(f"Error fetching positions for {trader_address}: {e}")
            return {}

    def _get_last_snapshot(self, trader_address: str) -> Dict:
        """Get the most recent position snapshot for a trader"""

        with self.engine.connect() as conn:
            query = text("""
                SELECT market_id, token_id, side, size, avg_price, market_name
                FROM position_snapshots
                WHERE trader_address = :trader_address
                AND snapshot_time = (
                    SELECT MAX(snapshot_time)
                    FROM position_snapshots
                    WHERE trader_address = :trader_address
                )
            """)

            result = conn.execute(query, {"trader_address": trader_address})
            rows = result.fetchall()

            snapshot = {}
            for row in rows:
                key = f"{row.market_id}_{row.token_id}"
                snapshot[key] = {
                    'market_id': row.market_id,
                    'market_name': row.market_name,
                    'token_id': row.token_id,
                    'side': row.side,
                    'size': float(row.size),
                    'avg_price': float(row.avg_price)
                }

            return snapshot

    def _save_snapshot(self, trader_address: str, positions: Dict):
        """Save current positions as a snapshot"""

        with self.engine.connect() as conn:
            for key, pos in positions.items():
                query = text("""
                    INSERT INTO position_snapshots
                    (trader_address, market_id, market_name, token_id, side, size, avg_price)
                    VALUES
                    (:trader_address, :market_id, :market_name, :token_id, :side, :size, :avg_price)
                """)

                conn.execute(query, {
                    "trader_address": trader_address,
                    "market_id": pos['market_id'],
                    "market_name": pos['market_name'],
                    "token_id": pos['token_id'],
                    "side": pos['side'],
                    "size": pos['size'],
                    "avg_price": pos['avg_price']
                })

            conn.commit()

    def _detect_position_changes(self, old_snapshot: Dict, new_snapshot: Dict) -> List[Dict]:
        """
        Detect changes between old and new snapshots

        Returns:
            List of change dicts with type, action, market_id, etc.
        """

        changes = []

        # Check for new positions and size increases
        for key, new_pos in new_snapshot.items():
            old_pos = old_snapshot.get(key)

            if not old_pos:
                # NEW POSITION
                changes.append({
                    'type': 'NEW_POSITION',
                    'action': 'BUY',
                    **new_pos,
                    'size_change': new_pos['size']
                })
            elif new_pos['size'] > old_pos['size']:
                # SIZE INCREASE
                size_delta = new_pos['size'] - old_pos['size']
                changes.append({
                    'type': 'SIZE_INCREASE',
                    'action': 'BUY',
                    **new_pos,
                    'size_change': size_delta
                })
            elif new_pos['size'] < old_pos['size']:
                # SIZE DECREASE
                size_delta = old_pos['size'] - new_pos['size']
                changes.append({
                    'type': 'SIZE_DECREASE',
                    'action': 'SELL',
                    **new_pos,
                    'size_change': size_delta,
                    'avg_price': old_pos['avg_price']  # Use old price for sells
                })

        # Check for closed positions
        for key, old_pos in old_snapshot.items():
            if key not in new_snapshot:
                # POSITION CLOSED
                changes.append({
                    'type': 'POSITION_CLOSED',
                    'action': 'SELL',
                    **old_pos,
                    'size_change': old_pos['size']
                })

        return changes

    async def _execute_copy_trade(self, config: Dict, change: Dict):
        """
        Execute a copy trade based on detected change

        Args:
            config: Copy trading configuration
            change: Detected position change
        """

        copy_percentage = float(config['copy_percentage']) / 100
        target_size = float(change['size_change'])
        target_price = float(change['avg_price'])

        # Calculate proportional size
        user_size = target_size * copy_percentage

        # Check minimum size
        notional_value = user_size * target_price
        if notional_value < self.MIN_TRADE_SIZE:
            logger.info(
                f"Skipping trade: below minimum (${notional_value:.2f} < ${self.MIN_TRADE_SIZE})"
            )
            return

        # Check if we should cancel pending order if trader changed mind
        if change['action'] == 'SELL':
            await self._cancel_pending_buy_orders(
                config['user_wallet_address'],
                change['market_id'],
                change['token_id']
            )

        # Get current market data
        market_data = self.clob_client.get_market_data(change['token_id'])

        # Calculate optimal price
        pricing = self.pricing_engine.calculate_optimal_price(
            target_price=target_price,
            order_side=change['action'],
            market_data=market_data,
            hours_elapsed=0  # New order
        )

        logger.info(
            f"Creating {change['action']} order: {user_size:.2f} shares @ ${pricing['price']:.4f} "
            f"(target: ${target_price:.4f}, urgency: {pricing['urgency']})"
        )

        try:
            # Create and submit order
            if pricing['order_type'] == 'MARKET':
                # Market order
                order_result = await self._create_market_order(
                    token_id=change['token_id'],
                    side=change['side'],
                    order_side=change['action'],
                    amount=notional_value
                )
            else:
                # Limit order
                order_result = await self._create_limit_order(
                    token_id=change['token_id'],
                    side=change['side'],
                    order_side=change['action'],
                    size=user_size,
                    price=pricing['price']
                )

            # Save to pending_copy_orders
            self._save_pending_order(
                config=config,
                change=change,
                user_size=user_size,
                pricing=pricing,
                order_id=order_result.get('order_id')
            )

            logger.info(f"✅ Copy trade executed successfully: {order_result.get('order_id')}")

        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            raise

    async def _create_limit_order(self, token_id: str, side: str, order_side: str, size: float, price: float) -> Dict:
        """Create and submit a limit order"""

        order_data = self.clob_client.create_limit_order(
            token_id=token_id,
            side=side,
            order_side=order_side,
            size=size,
            price=price
        )

        from py_clob_client.clob_types import OrderType
        result = self.clob_client.post_order(order_data, OrderType.GTC)

        return result

    async def _create_market_order(self, token_id: str, side: str, order_side: str, amount: float) -> Dict:
        """Create and submit a market order"""

        order_data = self.clob_client.create_market_order(
            token_id=token_id,
            side=side,
            order_side=order_side,
            amount=amount
        )

        from py_clob_client.clob_types import OrderType
        result = self.clob_client.post_order(order_data, OrderType.FOK)

        return result

    def _save_pending_order(self, config: Dict, change: Dict, user_size: float, pricing: Dict, order_id: str):
        """Save pending order to database"""

        with self.engine.connect() as conn:
            query = text("""
                INSERT INTO pending_copy_orders
                (user_wallet_address, target_trader_address, target_trader_name,
                 market_id, market_name, token_id, side, order_side,
                 target_size, target_price, initial_price, current_price, clob_order_id)
                VALUES
                (:user_wallet, :target_trader, :trader_name,
                 :market_id, :market_name, :token_id, :side, :order_side,
                 :target_size, :target_price, :initial_price, :current_price, :order_id)
            """)

            conn.execute(query, {
                "user_wallet": config['user_wallet_address'],
                "target_trader": config['target_trader_address'],
                "trader_name": config['target_trader_name'],
                "market_id": change['market_id'],
                "market_name": change.get('market_name', ''),
                "token_id": change['token_id'],
                "side": change['side'],
                "order_side": change['action'],
                "target_size": user_size,
                "target_price": change['avg_price'],
                "initial_price": pricing['price'],
                "current_price": pricing['price'],
                "order_id": order_id
            })

            conn.commit()

    async def _cancel_pending_buy_orders(self, user_wallet: str, market_id: str, token_id: str):
        """Cancel pending BUY orders for a market if trader is now selling"""

        with self.engine.connect() as conn:
            # Get pending buy orders for this market
            query = text("""
                SELECT id, clob_order_id
                FROM pending_copy_orders
                WHERE user_wallet_address = :user_wallet
                AND market_id = :market_id
                AND token_id = :token_id
                AND order_side = 'BUY'
                AND status IN ('pending', 'partial')
            """)

            result = conn.execute(query, {
                "user_wallet": user_wallet,
                "market_id": market_id,
                "token_id": token_id
            })

            pending_orders = result.fetchall()

            for order in pending_orders:
                try:
                    # Cancel on CLOB
                    if order.clob_order_id:
                        self.clob_client.cancel_order(order.clob_order_id)

                    # Mark as cancelled in DB
                    update_query = text("""
                        UPDATE pending_copy_orders
                        SET status = 'cancelled', last_updated = NOW()
                        WHERE id = :order_id
                    """)

                    conn.execute(update_query, {"order_id": order.id})

                    logger.info(f"Cancelled pending BUY order (trader now selling)")

                except Exception as e:
                    logger.error(f"Failed to cancel order {order.id}: {e}")

            conn.commit()

    async def manage_pending_orders(self):
        """
        Manage all pending orders - runs every 5 minutes
        - Check order status
        - Adjust prices if necessary
        - Convert to market orders after 36h
        """

        logger.info("🔧 Managing pending orders...")

        try:
            pending_orders = self._get_pending_orders()

            if not pending_orders:
                logger.info("No pending orders to manage")
                return

            logger.info(f"Managing {len(pending_orders)} pending order(s)")

            for order in pending_orders:
                try:
                    await self._manage_single_order(order)
                except Exception as e:
                    logger.error(f"Error managing order {order['id']}: {e}")

            logger.info("✅ Pending orders management completed")

        except Exception as e:
            logger.error(f"Error in manage_pending_orders: {e}")

    def _get_pending_orders(self) -> List[Dict]:
        """Get all pending or partial orders"""

        with self.engine.connect() as conn:
            query = text("""
                SELECT *
                FROM pending_copy_orders
                WHERE status IN ('pending', 'partial')
                ORDER BY created_at ASC
            """)

            result = conn.execute(query)
            rows = result.fetchall()

            return [dict(row._mapping) for row in rows]

    async def _manage_single_order(self, order: Dict):
        """Manage a single pending order"""

        order_id = order['clob_order_id']

        # Check order status on CLOB
        status = self.clob_client.get_order_status(order_id)

        if not status:
            logger.warning(f"Could not get status for order {order_id}")
            return

        # Check if filled
        if status['status'] == 'FILLED':
            self._mark_order_filled(order, status)
            return

        # Calculate time elapsed
        created_at = order['created_at']
        hours_elapsed = (datetime.utcnow() - created_at).total_seconds() / 3600

        # Check if we should adjust price
        should_adjust = self.pricing_engine.should_adjust_price(
            order_created_at=created_at,
            last_adjustment=order.get('last_price_adjustment'),
            adjustment_count=order['price_adjustment_count']
        )

        if should_adjust:
            await self._adjust_order_price(order, hours_elapsed)

    def _mark_order_filled(self, order: Dict, status: Dict):
        """Mark order as filled and move to executed_copy_trades"""

        with self.engine.connect() as conn:
            # Update pending order
            update_query = text("""
                UPDATE pending_copy_orders
                SET status = 'filled',
                    filled_size = :filled_size,
                    last_updated = NOW()
                WHERE id = :order_id
            """)

            conn.execute(update_query, {
                "filled_size": status['filled_size'],
                "order_id": order['id']
            })

            # Insert into executed trades
            insert_query = text("""
                INSERT INTO executed_copy_trades
                (user_wallet_address, target_trader_address, target_trader_name,
                 market_id, market_name, token_id, side, order_side,
                 size, price, target_price, slippage, clob_order_id)
                VALUES
                (:user_wallet, :target_trader, :trader_name,
                 :market_id, :market_name, :token_id, :side, :order_side,
                 :size, :price, :target_price, :slippage, :order_id)
            """)

            slippage = float(order['current_price']) - float(order['target_price'])

            conn.execute(insert_query, {
                "user_wallet": order['user_wallet_address'],
                "target_trader": order['target_trader_address'],
                "trader_name": order['target_trader_name'],
                "market_id": order['market_id'],
                "market_name": order['market_name'],
                "token_id": order['token_id'],
                "side": order['side'],
                "order_side": order['order_side'],
                "size": status['filled_size'],
                "price": order['current_price'],
                "target_price": order['target_price'],
                "slippage": slippage,
                "order_id": order['clob_order_id']
            })

            conn.commit()

            logger.info(f"✅ Order filled: {status['filled_size']} shares @ ${order['current_price']}")

    async def _adjust_order_price(self, order: Dict, hours_elapsed: float):
        """Adjust order price based on smart pricing algorithm"""

        # Get current market data
        market_data = self.clob_client.get_market_data(order['token_id'])

        # Calculate new optimal price
        pricing = self.pricing_engine.calculate_optimal_price(
            target_price=float(order['target_price']),
            order_side=order['order_side'],
            market_data=market_data,
            hours_elapsed=hours_elapsed
        )

        if pricing['order_type'] == 'MARKET':
            # Convert to market order
            logger.info(f"Converting order {order['id']} to market order (36h+ elapsed)")
            await self._convert_to_market_order(order)
        elif abs(pricing['price'] - float(order['current_price'])) > 0.001:
            # Price changed significantly, cancel and recreate
            logger.info(
                f"Adjusting order {order['id']} price: "
                f"${order['current_price']:.4f} → ${pricing['price']:.4f}"
            )
            await self._recreate_order_with_new_price(order, pricing['price'])

    async def _convert_to_market_order(self, order: Dict):
        """Convert limit order to market order"""

        try:
            # Cancel existing limit order
            if order['clob_order_id']:
                self.clob_client.cancel_order(order['clob_order_id'])

            # Create market order
            notional = float(order['target_size']) * float(order['target_price'])

            result = await self._create_market_order(
                token_id=order['token_id'],
                side=order['side'],
                order_side=order['order_side'],
                amount=notional
            )

            # Update in database
            with self.engine.connect() as conn:
                query = text("""
                    UPDATE pending_copy_orders
                    SET clob_order_id = :new_order_id,
                        last_updated = NOW()
                    WHERE id = :order_id
                """)

                conn.execute(query, {
                    "new_order_id": result.get('order_id'),
                    "order_id": order['id']
                })

                conn.commit()

            logger.info(f"✅ Converted to market order: {result.get('order_id')}")

        except Exception as e:
            logger.error(f"Failed to convert to market order: {e}")

    async def _recreate_order_with_new_price(self, order: Dict, new_price: float):
        """Cancel existing order and recreate with new price"""

        try:
            # Cancel existing order
            if order['clob_order_id']:
                self.clob_client.cancel_order(order['clob_order_id'])

            # Create new order with adjusted price
            result = await self._create_limit_order(
                token_id=order['token_id'],
                side=order['side'],
                order_side=order['order_side'],
                size=float(order['target_size']),
                price=new_price
            )

            # Update in database
            with self.engine.connect() as conn:
                query = text("""
                    UPDATE pending_copy_orders
                    SET clob_order_id = :new_order_id,
                        current_price = :new_price,
                        price_adjustment_count = price_adjustment_count + 1,
                        last_price_adjustment = NOW(),
                        last_updated = NOW()
                    WHERE id = :order_id
                """)

                conn.execute(query, {
                    "new_order_id": result.get('order_id'),
                    "new_price": new_price,
                    "order_id": order['id']
                })

                conn.commit()

            logger.info(f"✅ Order price adjusted to ${new_price:.4f}")

        except Exception as e:
            logger.error(f"Failed to recreate order: {e}")

    def _get_active_configs(self) -> List[Dict]:
        """Get all active copy trading configurations"""

        with self.engine.connect() as conn:
            query = text("""
                SELECT *
                FROM copy_trading_config
                WHERE enabled = true
            """)

            result = conn.execute(query)
            rows = result.fetchall()

            return [dict(row._mapping) for row in rows]


# Global instance - lazy initialization
# Only create instance if environment variables are set
_copy_trading_engine_instance = None

def get_copy_trading_engine():
    """Get or create the copy trading engine instance"""
    global _copy_trading_engine_instance
    if _copy_trading_engine_instance is None:
        _copy_trading_engine_instance = CopyTradingEngine()
    return _copy_trading_engine_instance

# Try to create instance, but don't fail if env vars not set
copy_trading_engine = None
try:
    import os

    # Debug: Log what Railway sees
    private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
    wallet_address = os.getenv("POLYMARKET_WALLET_ADDRESS")

    print(f"[DEBUG] POLYMARKET_PRIVATE_KEY present: {bool(private_key)}")
    print(f"[DEBUG] POLYMARKET_WALLET_ADDRESS present: {bool(wallet_address)}")

    if private_key:
        print("[INFO] Initializing Copy Trading Engine...")
        copy_trading_engine = CopyTradingEngine()
        print("[SUCCESS] Copy Trading Engine initialized!")
    else:
        print("[WARNING] POLYMARKET_PRIVATE_KEY not found in environment variables")
except (ValueError, Exception) as e:
    # Environment variables not set - copy trading will be disabled
    print(f"[ERROR] Copy trading engine initialization failed: {e}")
    import traceback
    traceback.print_exc()
    pass
