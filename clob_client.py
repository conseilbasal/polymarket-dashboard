"""
Polymarket CLOB Client Wrapper
Handles authentication, order creation, and market data fetching
"""

import os
import logging
from typing import Dict, List, Optional
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, MarketOrderArgs
from py_clob_client.order_builder.constants import BUY, SELL

logger = logging.getLogger(__name__)

class PolymarketCLOBClient:
    """
    Wrapper around py-clob-client for easier integration
    Handles authentication, order management, and market data
    """

    def __init__(self):
        """Initialize the CLOB client with credentials from environment"""

        # Get credentials from environment variables
        self.private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
        self.wallet_address = os.getenv("POLYMARKET_WALLET_ADDRESS")
        self.api_key = os.getenv("POLYMARKET_BUILDER_API_KEY")

        if not self.private_key:
            raise ValueError("POLYMARKET_PRIVATE_KEY environment variable not set")

        if not self.wallet_address:
            raise ValueError("POLYMARKET_WALLET_ADDRESS environment variable not set")

        # Initialize Polymarket CLOB client
        # host: Polymarket CLOB API endpoint
        # key: Private key for signing orders
        # chain_id: 137 for Polygon mainnet
        self.client = ClobClient(
            host="https://clob.polymarket.com",
            key=self.private_key,
            chain_id=137,  # Polygon mainnet
            signature_type=0,  # EOA (Externally Owned Account)
            funder=self.wallet_address
        )

        logger.info(f"✅ CLOB Client initialized for wallet: {self.wallet_address[:8]}...{self.wallet_address[-6:]}")

    def create_limit_order(
        self,
        token_id: str,
        side: str,  # 'YES' or 'NO'
        order_side: str,  # 'BUY' or 'SELL'
        size: float,
        price: float
    ) -> Dict:
        """
        Create a limit order

        Args:
            token_id: Token ID from market (YES or NO token)
            side: 'YES' or 'NO' (which outcome)
            order_side: 'BUY' or 'SELL'
            size: Number of shares
            price: Price per share (0-1 range, e.g., 0.58 for 58¢)

        Returns:
            Dict with order details and signature
        """

        try:
            # Convert to py-clob-client format
            clob_side = BUY if order_side == 'BUY' else SELL

            # Create order arguments
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=clob_side
            )

            # Create and sign the order
            signed_order = self.client.create_order(order_args)

            logger.info(
                f"Created limit order: {order_side} {size} shares @ ${price:.4f} "
                f"(token: {token_id[:8]}...)"
            )

            return {
                'order': signed_order,
                'token_id': token_id,
                'side': side,
                'order_side': order_side,
                'size': size,
                'price': price,
                'order_type': 'LIMIT'
            }

        except Exception as e:
            logger.error(f"Failed to create limit order: {e}")
            raise

    def create_market_order(
        self,
        token_id: str,
        side: str,
        order_side: str,
        amount: float  # Dollar amount to spend
    ) -> Dict:
        """
        Create a market order (executed immediately at best available price)

        Args:
            token_id: Token ID from market
            side: 'YES' or 'NO'
            order_side: 'BUY' or 'SELL'
            amount: Dollar amount to spend/receive

        Returns:
            Dict with order details
        """

        try:
            clob_side = BUY if order_side == 'BUY' else SELL

            # Market orders use FOK (Fill-Or-Kill)
            market_args = MarketOrderArgs(
                token_id=token_id,
                amount=amount,
                side=clob_side,
                order_type=OrderType.FOK  # Fill-Or-Kill
            )

            signed_order = self.client.create_market_order(market_args)

            logger.info(
                f"Created market order: {order_side} ${amount} worth "
                f"(token: {token_id[:8]}...)"
            )

            return {
                'order': signed_order,
                'token_id': token_id,
                'side': side,
                'order_side': order_side,
                'amount': amount,
                'order_type': 'MARKET'
            }

        except Exception as e:
            logger.error(f"Failed to create market order: {e}")
            raise

    def post_order(self, signed_order: Dict, order_type: OrderType = OrderType.GTC) -> Dict:
        """
        Submit an order to the CLOB

        Args:
            signed_order: Signed order from create_order() or create_market_order()
            order_type: GTC (Good-Til-Cancelled) or FOK (Fill-Or-Kill)

        Returns:
            Dict with order ID and status
        """

        try:
            response = self.client.post_order(signed_order['order'], order_type)

            logger.info(f"Posted order to CLOB: {response.get('orderID', 'unknown')}")

            return {
                'order_id': response.get('orderID'),
                'status': response.get('status'),
                'response': response
            }

        except Exception as e:
            logger.error(f"Failed to post order: {e}")
            raise

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order

        Args:
            order_id: Order ID from post_order()

        Returns:
            bool: True if cancelled successfully
        """

        try:
            response = self.client.cancel_order(order_id)
            logger.info(f"Cancelled order: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """
        Get status of an order

        Args:
            order_id: Order ID from post_order()

        Returns:
            Dict with order status or None if not found
        """

        try:
            response = self.client.get_order(order_id)

            return {
                'order_id': order_id,
                'status': response.get('status'),
                'filled_size': response.get('size_matched', 0),
                'remaining_size': response.get('size_remaining', 0),
                'price': response.get('price'),
                'details': response
            }

        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            return None

    def get_market_data(self, token_id: str) -> Dict:
        """
        Get current market data (bid/ask/spread)

        Args:
            token_id: Token ID

        Returns:
            Dict with bid, ask, mid, spread, spread_percentage
        """

        try:
            # Get order book for this token
            order_book = self.client.get_order_book(token_id)

            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])

            if not bids or not asks:
                logger.warning(f"No bids or asks for token {token_id}")
                return {
                    'best_bid': 0,
                    'best_ask': 1,
                    'mid_price': 0.5,
                    'spread': 1,
                    'spread_percentage': 100
                }

            # Best bid is highest buy price
            best_bid = float(bids[0]['price'])

            # Best ask is lowest sell price
            best_ask = float(asks[0]['price'])

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
            logger.error(f"Failed to get market data for {token_id}: {e}")
            # Return default spread
            return {
                'best_bid': 0.45,
                'best_ask': 0.55,
                'mid_price': 0.5,
                'spread': 0.1,
                'spread_percentage': 20
            }

    def get_user_positions(self, address: Optional[str] = None) -> List[Dict]:
        """
        Get positions for a wallet address

        Args:
            address: Wallet address (defaults to self.wallet_address)

        Returns:
            List of positions with market info
        """

        if not address:
            address = self.wallet_address

        try:
            positions = self.client.get_positions(address)

            formatted_positions = []
            for pos in positions:
                formatted_positions.append({
                    'market_id': pos.get('market'),
                    'token_id': pos.get('token_id'),
                    'side': pos.get('side'),
                    'size': float(pos.get('size', 0)),
                    'price': float(pos.get('price', 0)),
                    'value': float(pos.get('value', 0))
                })

            logger.info(f"Retrieved {len(formatted_positions)} positions for {address[:8]}...")
            return formatted_positions

        except Exception as e:
            logger.error(f"Failed to get positions for {address}: {e}")
            return []

    def get_balance(self) -> float:
        """
        Get USDC balance for the wallet

        Returns:
            float: USDC balance
        """

        try:
            balance = self.client.get_balance()
            usdc_balance = float(balance.get('balance', 0))
            logger.info(f"Wallet balance: ${usdc_balance:.2f} USDC")
            return usdc_balance

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0
