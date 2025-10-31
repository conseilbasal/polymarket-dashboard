"""
Smart Pricing Engine for Copy Trading
Adapts order prices based on market conditions, spread, and time elapsed
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SmartPricingEngine:
    """
    Intelligent pricing algorithm that:
    - Analyzes bid/ask spread to determine market liquidity
    - Adjusts prices progressively over time
    - Adapts strategy based on spread width (tight/normal/wide)
    - Ensures maximum execution probability while minimizing slippage
    """

    def __init__(self):
        # Configuration thresholds
        self.TIGHT_SPREAD_THRESHOLD = 0.5  # < 0.5% spread = very liquid market
        self.WIDE_SPREAD_THRESHOLD = 2.0   # > 2% spread = illiquid market

        # Time windows (in hours)
        self.TIME_WINDOW_1 = 6    # 0-6h: Patient, exact price
        self.TIME_WINDOW_2 = 12   # 6-12h: Start adjusting
        self.TIME_WINDOW_3 = 24   # 12-24h: Mid-market
        self.TIME_WINDOW_4 = 36   # 24-36h: Aggressive
        self.TIME_WINDOW_5 = 36   # 36h+: Market order

    def calculate_optimal_price(
        self,
        target_price: float,
        order_side: str,  # 'BUY' or 'SELL'
        market_data: Dict,
        hours_elapsed: float
    ) -> Dict:
        """
        Calculate optimal order price based on market conditions and time

        Args:
            target_price: Price at which the trader we're copying executed
            order_side: 'BUY' or 'SELL'
            market_data: {
                'best_bid': float,
                'best_ask': float,
                'mid_price': float,
                'spread': float,
                'spread_percentage': float
            }
            hours_elapsed: Hours since order was created

        Returns:
            {
                'price': float,
                'order_type': 'LIMIT' or 'MARKET',
                'urgency': 'low' | 'medium' | 'high' | 'critical',
                'reasoning': str
            }
        """

        bid = market_data['best_bid']
        ask = market_data['best_ask']
        spread = ask - bid
        spread_pct = market_data.get('spread_percentage', (spread / target_price) * 100)
        mid_price = (bid + ask) / 2

        # Determine market liquidity category
        if spread_pct < self.TIGHT_SPREAD_THRESHOLD:
            strategy_func = self._tight_spread_strategy
            liquidity = "high"
        elif spread_pct < self.WIDE_SPREAD_THRESHOLD:
            strategy_func = self._normal_spread_strategy
            liquidity = "normal"
        else:
            strategy_func = self._wide_spread_strategy
            liquidity = "low"

        # Calculate base strategy
        result = strategy_func(
            target_price=target_price,
            bid=bid,
            ask=ask,
            mid_price=mid_price,
            spread=spread,
            spread_pct=spread_pct,
            order_side=order_side,
            hours_elapsed=hours_elapsed
        )

        # Add metadata
        result['liquidity'] = liquidity
        result['spread_pct'] = round(spread_pct, 4)
        result['hours_elapsed'] = round(hours_elapsed, 2)

        logger.info(
            f"Pricing decision: {order_side} @ {result['price']:.4f} "
            f"(target: {target_price:.4f}, urgency: {result['urgency']}, "
            f"spread: {spread_pct:.2f}%, time: {hours_elapsed:.1f}h)"
        )

        return result

    def _tight_spread_strategy(
        self,
        target_price: float,
        bid: float,
        ask: float,
        mid_price: float,
        spread: float,
        spread_pct: float,
        order_side: str,
        hours_elapsed: float
    ) -> Dict:
        """
        Strategy for highly liquid markets (spread < 0.5%)
        Patient approach - stick close to target price, minimal slippage
        """

        if hours_elapsed < self.TIME_WINDOW_1:  # 0-6h
            # Very patient - exact trader price
            price = target_price
            urgency = 'low'
            reasoning = f"Tight spread ({spread_pct:.2f}%), being patient with exact price"

        elif hours_elapsed < self.TIME_WINDOW_2:  # 6-12h
            # Slightly more aggressive - move 10% toward best price
            if order_side == 'BUY':
                price = target_price + (spread * 0.1)
            else:  # SELL
                price = target_price - (spread * 0.1)
            urgency = 'low'
            reasoning = f"Tight spread, 6-12h elapsed, moving 10% toward market"

        elif hours_elapsed < self.TIME_WINDOW_3:  # 12-24h
            # Mid-market pricing
            if order_side == 'BUY':
                price = min(mid_price, target_price + spread * 0.3)
            else:  # SELL
                price = max(mid_price, target_price - spread * 0.3)
            urgency = 'medium'
            reasoning = f"Tight spread, 12-24h elapsed, using mid-market"

        elif hours_elapsed < self.TIME_WINDOW_4:  # 24-36h
            # Hit the best available price
            price = ask if order_side == 'BUY' else bid
            urgency = 'high'
            reasoning = f"Tight spread, 24-36h elapsed, hitting best price"

        else:  # 36h+
            # Market order for guaranteed execution
            price = None  # Market order
            urgency = 'critical'
            reasoning = f"36h+ elapsed, switching to market order"
            return {
                'price': price,
                'order_type': 'MARKET',
                'urgency': urgency,
                'reasoning': reasoning
            }

        return {
            'price': round(price, 8),
            'order_type': 'LIMIT',
            'urgency': urgency,
            'reasoning': reasoning
        }

    def _normal_spread_strategy(
        self,
        target_price: float,
        bid: float,
        ask: float,
        mid_price: float,
        spread: float,
        spread_pct: float,
        order_side: str,
        hours_elapsed: float
    ) -> Dict:
        """
        Strategy for normal liquidity markets (0.5% < spread < 2%)
        Balanced approach - moderate patience with progressive aggression
        """

        if hours_elapsed < self.TIME_WINDOW_1:  # 0-6h
            # Start with exact price
            price = target_price
            urgency = 'low'
            reasoning = f"Normal spread ({spread_pct:.2f}%), starting with exact price"

        elif hours_elapsed < self.TIME_WINDOW_2:  # 6-12h
            # Move 20% toward best price (more aggressive than tight spread)
            if order_side == 'BUY':
                price = target_price + (spread * 0.2)
            else:  # SELL
                price = target_price - (spread * 0.2)
            urgency = 'medium'
            reasoning = f"Normal spread, 6-12h elapsed, moving 20% toward market"

        elif hours_elapsed < self.TIME_WINDOW_3:  # 12-24h
            # Aggressive mid-market or better
            if order_side == 'BUY':
                price = mid_price + (spread * 0.1)  # Slightly above mid
            else:  # SELL
                price = mid_price - (spread * 0.1)  # Slightly below mid
            urgency = 'high'
            reasoning = f"Normal spread, 12-24h elapsed, aggressive mid-market"

        elif hours_elapsed < self.TIME_WINDOW_4:  # 24-36h
            # Hit best price + buffer for guaranteed fill
            if order_side == 'BUY':
                price = ask + (spread * 0.05)  # 5% above ask
            else:  # SELL
                price = bid - (spread * 0.05)  # 5% below bid
            urgency = 'high'
            reasoning = f"Normal spread, 24-36h elapsed, exceeding best price"

        else:  # 36h+
            # Market order
            price = None
            urgency = 'critical'
            reasoning = f"36h+ elapsed, market order for guaranteed execution"
            return {
                'price': price,
                'order_type': 'MARKET',
                'urgency': urgency,
                'reasoning': reasoning
            }

        return {
            'price': round(price, 8),
            'order_type': 'LIMIT',
            'urgency': urgency,
            'reasoning': reasoning
        }

    def _wide_spread_strategy(
        self,
        target_price: float,
        bid: float,
        ask: float,
        mid_price: float,
        spread: float,
        spread_pct: float,
        order_side: str,
        hours_elapsed: float
    ) -> Dict:
        """
        Strategy for illiquid markets (spread > 2%)
        Aggressive approach - accept more slippage to ensure execution
        """

        if hours_elapsed < 2:  # 0-2h (shorter window for illiquid markets)
            # Try exact price but don't wait long
            price = target_price
            urgency = 'medium'
            reasoning = f"Wide spread ({spread_pct:.2f}%), trying exact price briefly"

        elif hours_elapsed < self.TIME_WINDOW_1:  # 2-6h
            # Already moving toward market
            if order_side == 'BUY':
                price = target_price + (spread * 0.15)
            else:  # SELL
                price = target_price - (spread * 0.15)
            urgency = 'medium'
            reasoning = f"Wide spread, 2-6h elapsed, moving toward market"

        elif hours_elapsed < self.TIME_WINDOW_2:  # 6-12h
            # Aggressive mid-market
            price = mid_price
            urgency = 'high'
            reasoning = f"Wide spread, 6-12h elapsed, hitting mid-market"

        elif hours_elapsed < self.TIME_WINDOW_3:  # 12-24h
            # Hit best price or better
            if order_side == 'BUY':
                price = ask + (spread * 0.1)
            else:  # SELL
                price = bid - (spread * 0.1)
            urgency = 'high'
            reasoning = f"Wide spread, 12-24h elapsed, exceeding best price"

        else:  # 24h+ (faster market order for illiquid markets)
            # Market order sooner than liquid markets
            price = None
            urgency = 'critical'
            reasoning = f"Wide spread, 24h+ elapsed, market order"
            return {
                'price': price,
                'order_type': 'MARKET',
                'urgency': urgency,
                'reasoning': reasoning
            }

        return {
            'price': round(price, 8),
            'order_type': 'LIMIT',
            'urgency': urgency,
            'reasoning': reasoning
        }

    def should_adjust_price(
        self,
        order_created_at: datetime,
        last_adjustment: Optional[datetime],
        adjustment_count: int
    ) -> bool:
        """
        Determine if an order price should be adjusted

        Args:
            order_created_at: When the order was first created
            last_adjustment: When price was last adjusted (None if never)
            adjustment_count: Number of times price has been adjusted

        Returns:
            bool: True if price should be adjusted now
        """

        now = datetime.utcnow()
        hours_elapsed = (now - order_created_at).total_seconds() / 3600

        # No adjustments in first 6 hours
        if hours_elapsed < self.TIME_WINDOW_1:
            return False

        # First adjustment at 6h
        if adjustment_count == 0 and hours_elapsed >= self.TIME_WINDOW_1:
            return True

        # If already adjusted, wait at least 3 hours between adjustments
        if last_adjustment:
            hours_since_last = (now - last_adjustment).total_seconds() / 3600
            if hours_since_last < 3:
                return False

        # Adjust at key time windows
        time_windows = [
            self.TIME_WINDOW_1,   # 6h
            self.TIME_WINDOW_2,   # 12h
            self.TIME_WINDOW_3,   # 24h
            self.TIME_WINDOW_4,   # 36h
        ]

        for i, window in enumerate(time_windows):
            if hours_elapsed >= window and adjustment_count <= i:
                return True

        return False
