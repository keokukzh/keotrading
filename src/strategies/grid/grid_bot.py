"""
Grid Trading Bot
================

Grid trading strategy that places buy and sell orders at regular intervals
within a specified price range. Profits from price oscillations.

Features:
- Configurable grid levels (default 10)
- Configurable grid range percentage (default 5-10%)
- Auto-rebalancing when orders fill
- Profit calculation per grid level
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List
import time

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Status of a grid order."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass
class GridLevel:
    """A single grid level with its orders."""
    level_id: int
    price: float
    buy_order_id: Optional[str] = None
    sell_order_id: Optional[str] = None
    buy_filled: bool = False
    sell_filled: bool = False
    buy_filled_price: float = 0.0
    sell_filled_price: float = 0.0
    buy_filled_amount: float = 0.0
    sell_filled_amount: float = 0.0
    total_profit: float = 0.0
    
    @property
    def is_complete(self) -> bool:
        """Both buy and sell filled at this level."""
        return self.buy_filled and self.sell_filled


@dataclass
class GridConfig:
    """Configuration for grid trading."""
    # Grid parameters
    grid_levels: int = 10
    grid_range_pct: float = 5.0  # Range from lower to upper bound (%)
    grid_range_top_pct: float = 5.0  # Upper bound offset (optional)
    grid_range_bottom_pct: float = 5.0  # Lower bound offset (optional)
    
    # Capital allocation
    capital_per_level_usd: float = 20.0
    total_capital_usd: float = 200.0  # Total capital for grid
    
    # Trading
    order_type: str = "limit"
    post_only: bool = True
    
    # Auto-rebalance
    auto_rebalance: bool = True
    rebalance_threshold_pct: float = 10.0  # Rebalance when P&L deviates by this %
    
    # Fees (for profit calculation)
    maker_fee: float = 0.001  # 0.1%
    taker_fee: float = 0.001  # 0.1%


@dataclass
class GridState:
    """Current state of the grid."""
    grid_id: str
    pair: str
    exchange: str
    lower_bound: float
    upper_bound: float
    current_price: float
    levels: List[GridLevel]
    total_invested: float = 0.0
    total_profit: float = 0.0
    base_asset_balance: float = 0.0
    quote_asset_balance: float = 0.0
    start_time: float = field(default_factory=time.time)
    
    @property
    def grid_range_pct(self) -> float:
        if self.lower_bound > 0:
            return ((self.upper_bound - self.lower_bound) / self.lower_bound) * 100
        return 0.0
    
    @property
    def price_in_grid(self) -> bool:
        return self.lower_bound <= self.current_price <= self.upper_bound
    
    @property
    def completion_rate(self) -> float:
        """Percentage of completed grid levels."""
        if not self.levels:
            return 0.0
        completed = sum(1 for lvl in self.levels if lvl.is_complete)
        return completed / len(self.levels)


@dataclass
class GridOrder:
    """Represents a grid order."""
    order_id: str
    level_id: int
    side: str  # "buy" or "sell"
    price: float
    amount: float
    filled_amount: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: float = field(default_factory=time.time)
    filled_at: Optional[float] = None


class GridBot:
    """
    Grid trading bot implementation.
    
    Places a grid of buy and sell orders between a lower and upper price bound.
    When buy orders fill, corresponding sell orders are placed at higher prices.
    When sell orders fill, corresponding buy orders are placed at lower prices.
    
    Profiting from grid trading:
    - Buy low, sell high within each grid cell
    - Accumulate small profits per completed grid cycle
    - The narrower the grid, the more trades but smaller profit per trade
    """
    
    def __init__(
        self,
        config: Optional[GridConfig] = None,
        pair: str = "BTC/USDT",
        exchange: str = "binance",
        grid_id: Optional[str] = None,
    ):
        """
        Initialize grid bot.
        
        Args:
            config: Grid configuration
            pair: Trading pair
            exchange: Exchange name
            grid_id: Optional grid identifier
        """
        self.config = config or GridConfig()
        self.pair = pair
        self.exchange = exchange
        self.grid_id = grid_id or f"grid_{pair.replace('/', '_')}_{int(time.time())}"
        
        # State
        self.state: Optional[GridState] = None
        self.orders: Dict[str, GridOrder] = {}
        
        logger.info(
            f"Initialized GridBot for {pair} on {exchange}, "
            f"levels={self.config.grid_levels}, range={self.config.grid_range_pct}%"
        )
    
    def validate_config(self) -> tuple[bool, str]:
        """
        Validate grid configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.config.grid_levels < 2:
            return False, f"Grid levels must be >= 2, got {self.config.grid_levels}"
        if self.config.grid_range_pct <= 0:
            return False, f"Grid range must be > 0"
        if self.config.capital_per_level_usd <= 0:
            return False, f"Capital per level must be > 0"
        if self.config.total_capital_usd < self.config.capital_per_level_usd * self.config.grid_levels:
            return False, "Total capital insufficient for grid configuration"
        
        return True, "Valid"
    
    def initialize_grid(
        self,
        current_price: float,
        lower_bound: Optional[float] = None,
        upper_bound: Optional[float] = None,
    ) -> GridState:
        """
        Initialize the grid with price bounds.
        
        Args:
            current_price: Current market price
            lower_bound: Lower price bound (None = auto from grid_range_pct)
            upper_bound: Upper price bound (None = auto from grid_range_pct)
            
        Returns:
            Initialized GridState
        """
        # Calculate bounds if not provided
        if lower_bound is None:
            lower_bound = current_price * (1 - self.config.grid_range_pct / 100)
        if upper_bound is None:
            upper_bound = current_price * (1 + self.config.grid_range_pct / 100)
        
        # Ensure correct ordering
        if lower_bound > upper_bound:
            lower_bound, upper_bound = upper_bound, lower_bound
        
        # Create grid levels
        price_step = (upper_bound - lower_bound) / (self.config.grid_levels - 1)
        levels = []
        
        for i in range(self.config.grid_levels):
            price = lower_bound + (price_step * i)
            levels.append(GridLevel(level_id=i, price=price))
        
        self.state = GridState(
            grid_id=self.grid_id,
            pair=self.pair,
            exchange=self.exchange,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            current_price=current_price,
            levels=levels,
            total_capital=self.config.total_capital_usd,
        )
        
        logger.info(
            f"Grid initialized: {lower_bound:.4f} - {upper_bound:.4f}, "
            f"{self.config.grid_levels} levels, step={price_step:.4f}"
        )
        
        return self.state
    
    def get_pending_orders(self) -> List[GridOrder]:
        """
        Get all pending orders to be placed.
        
        Returns:
            List of orders to place
        """
        pending = []
        
        for level in self.state.levels:
            # Check buy orders
            if not level.buy_filled and level.buy_order_id is None:
                # Calculate order amount based on capital per level
                amount = self._calculate_order_amount(level.price, "buy")
                pending.append(GridOrder(
                    order_id=f"{self.grid_id}_buy_{level.level_id}",
                    level_id=level.level_id,
                    side="buy",
                    price=level.price,
                    amount=amount,
                ))
            
            # Check sell orders (only after buy is filled)
            if level.buy_filled and not level.sell_filled and level.sell_order_id is None:
                amount = level.buy_filled_amount
                # Place sell at higher price
                sell_price = level.price * (1 + self.config.grid_range_pct / 100 / self.config.grid_levels)
                pending.append(GridOrder(
                    order_id=f"{self.grid_id}_sell_{level.level_id}",
                    level_id=level.level_id,
                    side="sell",
                    price=sell_price,
                    amount=amount,
                ))
        
        return pending
    
    def _calculate_order_amount(self, price: float, side: str) -> float:
        """Calculate order amount based on capital allocation."""
        # For buy orders, calculate how much base asset we can buy
        # For sell orders, calculate how much base asset we have
        if side == "buy":
            return self.config.capital_per_level_usd / price
        else:
            # Would use actual balance in real implementation
            return self.config.capital_per_level_usd / price
    
    def on_order_filled(
        self,
        order_id: str,
        filled_price: float,
        filled_amount: float,
        filled_side: str,
    ) -> dict:
        """
        Handle order fill event.
        
        Args:
            order_id: The filled order ID
            filled_price: Execution price
            filled_amount: Executed amount
            filled_side: "buy" or "sell"
            
        Returns:
            Dictionary with updated state info
        """
        logger.info(
            f"Order filled: {order_id}, side={filled_side}, "
            f"price={filled_price:.4f}, amount={filled_amount:.4f}"
        )
        
        # Parse order ID to get level and type
        parts = order_id.split('_')
        level_id = int(parts[-2])
        order_type = parts[-3]  # 'buy' or 'sell'
        
        level = self.state.levels[level_id]
        
        if order_type == "buy":
            # Buy order filled
            level.buy_filled = True
            level.buy_filled_price = filled_price
            level.buy_filled_amount = filled_amount
            level.buy_order_id = order_id
            
            # Update balances
            self.state.base_asset_balance += filled_amount
            self.state.quote_asset_balance -= filled_price * filled_amount
            
            # Place corresponding sell order at higher price
            sell_price = filled_price * (1 + self.config.grid_range_pct / 100 / self.config.grid_levels)
            sell_amount = filled_amount
            
            return {
                "action": "place_sell",
                "level_id": level_id,
                "sell_price": sell_price,
                "sell_amount": sell_amount,
            }
        
        elif order_type == "sell":
            # Sell order filled
            level.sell_filled = True
            level.sell_filled_price = filled_price
            level.sell_filled_amount = filled_amount
            level.sell_order_id = order_id
            
            # Calculate profit for this level
            buy_cost = level.buy_filled_price * level.buy_filled_amount
            sell_revenue = filled_price * filled_amount
            fees = (buy_cost + sell_revenue) * self.config.maker_fee
            profit = sell_revenue - buy_cost - fees
            
            level.total_profit = profit
            self.state.total_profit += profit
            
            # Update balances
            self.state.base_asset_balance -= filled_amount
            self.state.quote_asset_balance += sell_revenue - fees
            
            # Reset level for next grid cycle
            level.buy_filled = False
            level.sell_filled = False
            level.buy_filled_amount = 0.0
            level.sell_filled_amount = 0.0
            level.buy_order_id = None
            level.sell_order_id = None
            
            # Place new buy order at this level
            buy_amount = self._calculate_order_amount(level.price, "buy")
            
            return {
                "action": "place_buy",
                "level_id": level_id,
                "buy_price": level.price,
                "buy_amount": buy_amount,
            }
        
        return {"action": "none"}
    
    def calculate_profit_per_level(self) -> List[dict]:
        """
        Calculate profit breakdown per grid level.
        
        Returns:
            List of profit data per level
        """
        results = []
        
        for level in self.state.levels:
            if level.buy_filled and level.sell_filled:
                buy_cost = level.buy_filled_price * level.buy_filled_amount
                sell_revenue = level.sell_filled_price * level.sell_filled_amount
                fees = (buy_cost + sell_revenue) * self.config.maker_fee
                gross_profit = sell_revenue - buy_cost
                net_profit = gross_profit - fees
                
                results.append({
                    "level_id": level.level_id,
                    "price": level.price,
                    "buy_price": level.buy_filled_price,
                    "sell_price": level.sell_filled_price,
                    "buy_amount": level.buy_filled_amount,
                    "sell_amount": level.sell_filled_amount,
                    "buy_cost": buy_cost,
                    "sell_revenue": sell_revenue,
                    "gross_profit": gross_profit,
                    "net_profit": net_profit,
                    "fees": fees,
                    "complete": True,
                })
            else:
                results.append({
                    "level_id": level.level_id,
                    "price": level.price,
                    "complete": False,
                })
        
        return results
    
    def update_current_price(self, current_price: float):
        """
        Update current price and check if rebalancing is needed.
        
        Args:
            current_price: Current market price
        """
        old_price = self.state.current_price
        self.state.current_price = current_price
        
        logger.debug(f"Price updated: {old_price:.4f} -> {current_price:.4f}")
        
        # Check if price has left the grid
        if not self.state.price_in_grid:
            logger.warning(
                f"Price {current_price:.4f} outside grid bounds "
                f"[{self.state.lower_bound:.4f}, {self.state.upper_bound:.4f}]"
            )
            
            if self.config.auto_rebalance:
                self._rebalance_grid(current_price)
    
    def _rebalance_grid(self, current_price: float):
        """
        Rebalance the grid when price moves outside bounds.
        
        Args:
            current_price: Current market price
        """
        logger.info(f"Rebalancing grid around {current_price:.4f}")
        
        # Calculate new bounds centered on current price
        range_pct = self.config.grid_range_pct
        lower = current_price * (1 - range_pct / 100)
        upper = current_price * (1 + range_pct / 100)
        
        # Recalculate grid levels
        price_step = (upper - lower) / (self.config.grid_levels - 1)
        
        for i, level in enumerate(self.state.levels):
            level.level_id = i
            level.price = lower + (price_step * i)
            # Note: Existing filled orders at this level should be tracked separately
        
        self.state.lower_bound = lower
        self.state.upper_bound = upper
        
        logger.info(
            f"Grid rebalanced: [{lower:.4f}, {upper:.4f}], "
            f"step={price_step:.4f}"
        )
    
    def get_status(self) -> dict:
        """
        Get current grid status.
        
        Returns:
            Dictionary with grid status information
        """
        if not self.state:
            return {"initialized": False}
        
        completed_levels = sum(1 for l in self.state.levels if l.is_complete)
        
        return {
            "initialized": True,
            "grid_id": self.grid_id,
            "pair": self.pair,
            "exchange": self.exchange,
            "lower_bound": self.state.lower_bound,
            "upper_bound": self.state.upper_bound,
            "current_price": self.state.current_price,
            "grid_range_pct": self.state.grid_range_pct,
            "total_levels": len(self.state.levels),
            "completed_levels": completed_levels,
            "completion_rate": self.state.completion_rate,
            "total_profit": self.state.total_profit,
            "base_asset_balance": self.state.base_asset_balance,
            "quote_asset_balance": self.state.quote_asset_balance,
            "price_in_grid": self.state.price_in_grid,
            "uptime_seconds": time.time() - self.state.start_time,
        }
    
    def get_signal(self, market_data) -> dict:
        """
        Generate signal for grid trading.
        
        For grid trading, signals indicate:
        - Grid status
        - Recommended actions
        
        Returns:
            Dictionary with grid status and actions
        """
        if not self.state:
            return {"action": "initialize", "message": "Grid not initialized"}
        
        status = self.get_status()
        pending_orders = self.get_pending_orders()
        profit_per_level = self.calculate_profit_per_level()
        
        return {
            "action": "hold",
            "status": status,
            "pending_orders": len(pending_orders),
            "profit_per_level": profit_per_level,
            "message": f"Grid active with {status['completed_levels']}/{status['total_levels']} levels complete",
        }
