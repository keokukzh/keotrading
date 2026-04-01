"""
Virtual Portfolio & Order Management
===================================
Simulated portfolio for demo trading.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class VirtualPosition:
    """A position in the virtual portfolio."""
    symbol: str           # e.g., "BTC/USDT"
    quantity: float      # Amount held
    avg_cost: float      # Average entry price
    current_price: float = 0  # Updated from market
    unrealized_pnl: float = 0  # Calculated
    source: str = "demo"       # Exchange source
    opened_at: str = ""         # ISO timestamp
    
    def calculate_pnl(self):
        """Calculate unrealized P&L."""
        if self.current_price > 0 and self.avg_cost > 0:
            self.unrealized_pnl = (self.current_price - self.avg_cost) * self.quantity
        return self.unrealized_pnl
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_cost": self.avg_cost,
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "market_value": self.quantity * self.current_price,
            "source": self.source,
            "opened_at": self.opened_at,
        }


@dataclass
class VirtualOrder:
    """A simulated order."""
    id: str
    symbol: str
    side: str  # "buy" or "sell"
    order_type: str  # "market" or "limit"
    price: float  # Limit price (for limit orders)
    quantity: float
    filled_quantity: float = 0
    filled_price: float = 0
    status: str = "pending"  # pending, filled, cancelled, rejected
    slippage: float = 0
    fee: float = 0
    pnl: float = 0  # For closed positions
    created_at: str = ""
    filled_at: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "price": self.price,
            "quantity": self.quantity,
            "filled_quantity": self.filled_quantity,
            "filled_price": self.filled_price,
            "status": self.status,
            "slippage": self.slippage,
            "fee": self.fee,
            "pnl": self.pnl,
            "created_at": self.created_at,
            "filled_at": self.filled_at,
            "error": self.error,
        }


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""
    initial_balance: float = 100_000
    current_equity: float = 100_000
    cash: float = 100_000
    position_value: float = 0
    unrealized_pnl: float = 0
    realized_pnl: float = 0
    total_pnl: float = 0
    total_return_pct: float = 0
    trade_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    win_rate: float = 0
    max_drawdown: float = 0
    sharpe_ratio: float = 0
    avg_trade_pnl: float = 0


class VirtualPortfolio:
    """
    Virtual portfolio for demo trading.
    Tracks positions, orders, and calculates metrics.
    """
    
    DEFAULT_INITIAL_BALANCE = 100_000  # $100k
    
    def __init__(self, data_dir: str = "data/demo", initial_balance: float = 100_000):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.initial_balance = initial_balance
        self.orders_file = self.data_dir / "orders.jsonl"
        self.portfolio_file = self.data_dir / "portfolio.json"
        self.equity_file = self.data_dir / "equity_curve.json"
        
        # State
        self.cash = initial_balance
        self.positions: Dict[str, VirtualPosition] = {}
        self.orders: List[VirtualOrder] = []
        self.equity_curve: List[Dict] = []
        
        # Metrics
        self.metrics = PortfolioMetrics(initial_balance=initial_balance, cash=initial_balance)
        
        # Load existing state
        self._load()
    
    def _load(self):
        """Load portfolio state from disk."""
        # Load orders
        if self.orders_file.exists():
            try:
                with open(self.orders_file) as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            order = VirtualOrder(**data)
                            self.orders.append(order)
            except Exception as e:
                logger.error(f"Error loading orders: {e}")
        
        # Load portfolio
        if self.portfolio_file.exists():
            try:
                with open(self.portfolio_file) as f:
                    data = json.load(f)
                    self.cash = data.get("cash", self.initial_balance)
                    self.initial_balance = data.get("initial_balance", self.initial_balance)
                    for pos_data in data.get("positions", []):
                        pos = VirtualPosition(**pos_data)
                        self.positions[pos.symbol] = pos
            except Exception as e:
                logger.error(f"Error loading portfolio: {e}")
        
        # Load equity curve
        if self.equity_file.exists():
            try:
                with open(self.equity_file) as f:
                    self.equity_curve = json.load(f)
            except Exception as e:
                logger.error(f"Error loading equity curve: {e}")
        
        self._recalculate()
    
    def _save(self):
        """Save portfolio state to disk."""
        # Save orders (append to JSONL)
        with open(self.orders_file, 'a') as f:
            for order in self.orders[-100:]:  # Keep last 100
                f.write(json.dumps(order.to_dict()) + '\n')
        
        # Save portfolio
        portfolio_data = {
            "cash": self.cash,
            "initial_balance": self.initial_balance,
            "positions": [p.to_dict() for p in self.positions.values()],
            "saved_at": datetime.now().isoformat(),
        }
        with open(self.portfolio_file, 'w') as f:
            json.dump(portfolio_data, f, indent=2)
        
        # Save equity curve
        with open(self.equity_file, 'w') as f:
            json.dump(self.equity_curve[-365:], f, indent=2)  # Keep last year
    
    def _recalculate(self):
        """Recalculate all metrics."""
        # Calculate position values
        position_value = 0
        unrealized_pnl = 0
        
        for pos in self.positions.values():
            pos.calculate_pnl()
            position_value += pos.quantity * pos.current_price
            unrealized_pnl += pos.unrealized_pnl
        
        # Calculate realized P&L from closed trades
        realized_pnl = sum(o.pnl for o in self.orders if o.status == "filled" and o.side == "sell")
        
        # Current equity
        current_equity = self.cash + position_value
        total_pnl = current_equity - self.initial_balance
        total_return_pct = (total_pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0
        
        # Trade statistics
        closed_orders = [o for o in self.orders if o.status == "filled" and o.side == "sell"]
        win_count = sum(1 for o in closed_orders if o.pnl > 0)
        loss_count = sum(1 for o in closed_orders if o.pnl < 0)
        trade_count = len(closed_orders)
        win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0
        avg_trade_pnl = (realized_pnl / trade_count) if trade_count > 0 else 0
        
        # Max drawdown
        max_drawdown = 0
        if self.equity_curve:
            peak = self.initial_balance
            for entry in self.equity_curve:
                equity = entry.get("equity", current_equity)
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak * 100 if peak > 0 else 0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        # Update metrics
        self.metrics = PortfolioMetrics(
            initial_balance=self.initial_balance,
            current_equity=current_equity,
            cash=self.cash,
            position_value=position_value,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            total_pnl=total_pnl,
            total_return_pct=total_return_pct,
            trade_count=trade_count,
            win_count=win_count,
            loss_count=loss_count,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            avg_trade_pnl=avg_trade_pnl,
        )
    
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = 0,
    ) -> VirtualOrder:
        """Create a new order."""
        order = VirtualOrder(
            id=f"demo_{uuid.uuid4().hex[:12]}",
            symbol=symbol,
            side=side,
            order_type=order_type,
            price=price,
            quantity=quantity,
            created_at=datetime.now().isoformat(),
        )
        self.orders.append(order)
        return order
    
    def fill_order(
        self,
        order_id: str,
        filled_price: float,
        slippage: float = 0,
        fee: float = 0,
    ) -> bool:
        """Fill an order (simulate execution)."""
        order = next((o for o in self.orders if o.id == order_id), None)
        if not order or order.status != "pending":
            return False
        
        order.filled_price = filled_price
        order.filled_quantity = order.quantity
        order.slippage = slippage
        order.fee = fee
        order.status = "filled"
        order.filled_at = datetime.now().isoformat()
        
        # Update position
        position = self.positions.get(order.symbol)
        
        if order.side == "buy":
            # Buy order - add to position
            if position:
                # Update average cost
                total_cost = position.avg_cost * position.quantity
                new_cost = filled_price * order.quantity
                position.quantity += order.quantity
                position.avg_cost = (total_cost + new_cost) / position.quantity
            else:
                # New position
                self.positions[order.symbol] = VirtualPosition(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    avg_cost=filled_price,
                    current_price=filled_price,
                    opened_at=datetime.now().isoformat(),
                )
            
            # Deduct cash
            cost = filled_price * order.quantity + fee
            self.cash -= cost
            
        elif order.side == "sell":
            # Sell order - reduce position
            if position:
                # Calculate P&L
                pnl = (filled_price - position.avg_cost) * order.quantity - fee
                order.pnl = pnl
                
                position.quantity -= order.quantity
                if position.quantity <= 0:
                    del self.positions[order.symbol]
                
                # Add cash
                proceeds = filled_price * order.quantity - fee
                self.cash += proceeds
        
        self._recalculate()
        self._save()
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        order = next((o for o in self.orders if o.id == order_id), None)
        if not order or order.status != "pending":
            return False
        
        order.status = "cancelled"
        self._save()
        return True
    
    def update_prices(self, prices: Dict[str, float]):
        """Update current prices for all positions."""
        for symbol, price in prices.items():
            position = self.positions.get(symbol)
            if position:
                position.current_price = price
        self._recalculate()
        self._save()
    
    def record_equity(self):
        """Record current equity for curve."""
        entry = {
            "date": datetime.now().isoformat(),
            "equity": self.metrics.current_equity,
            "cash": self.metrics.cash,
            "position_value": self.metrics.position_value,
            "unrealized_pnl": self.metrics.unrealized_pnl,
            "realized_pnl": self.metrics.realized_pnl,
        }
        self.equity_curve.append(entry)
        # Keep last 365 entries
        self.equity_curve = self.equity_curve[-365:]
    
    def reset(self, initial_balance: float = 100_000):
        """Reset portfolio to initial state."""
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.positions = {}
        self.orders = []
        self.equity_curve = []
        self.metrics = PortfolioMetrics(
            initial_balance=initial_balance,
            cash=initial_balance,
        )
        
        # Clear files
        for f in [self.orders_file, self.portfolio_file, self.equity_file]:
            if f.exists():
                f.unlink()
        
        self._save()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get portfolio summary."""
        return {
            "metrics": asdict(self.metrics),
            "positions_count": len(self.positions),
            "positions": [p.to_dict() for p in self.positions.values()],
            "pending_orders": [o.to_dict() for o in self.orders if o.status == "pending"],
            "filled_orders_count": len([o for o in self.orders if o.status == "filled"]),
        }


# Global portfolio instance
_portfolio: Optional[VirtualPortfolio] = None


def get_virtual_portfolio() -> VirtualPortfolio:
    """Get or create virtual portfolio singleton."""
    global _portfolio
    if _portfolio is None:
        _portfolio = VirtualPortfolio()
    return _portfolio
