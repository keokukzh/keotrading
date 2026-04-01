"""
Order Execution Engine
Handles real order placement, position tracking, and trade history.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

from src.exchange.connection import ExchangeManager, ExchangeConnection

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass
class Order:
    """Represents a trading order."""
    order_id: str
    exchange_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    filled_amount: float = 0.0
    avg_fill_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    fee: float = 0.0
    fee_currency: str = "USDT"
    strategy: str = ""
    agent_id: str = ""
    notes: str = ""


@dataclass
class Position:
    """Represents an open position."""
    position_id: str
    exchange_id: str
    symbol: str
    side: OrderSide
    amount: float
    entry_price: float
    current_price: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    unrealized_pnl: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    orders: List[str] = field(default_factory=list)  # Order IDs
    strategy: str = ""
    agent_id: str = ""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class Trade:
    """Represents a completed trade."""
    trade_id: str
    order_id: str
    exchange_id: str
    symbol: str
    side: OrderSide
    amount: float
    price: float
    fee: float
    fee_currency: str
    executed_at: datetime
    strategy: str = ""
    agent_id: str = ""


class OrderExecutor:
    """
    Handles order execution across exchanges.
    Supports both paper trading and live trading modes.
    """
    
    def __init__(self, exchange_manager: ExchangeManager, paper_trading: bool = True):
        self.exchange_manager = exchange_manager
        self.paper_trading = paper_trading
        self._orders: Dict[str, Order] = {}
        self._positions: Dict[str, Position] = {}
        self._trades: List[Trade] = []
        self._order_id_counter = 0
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        self._order_id_counter += 1
        return f"ORD-{datetime.now().strftime('%Y%m%d')}-{self._order_id_counter:06d}"
    
    async def place_order(
        self,
        exchange_id: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        strategy: str = "",
        agent_id: str = "",
        notes: str = ""
    ) -> Order:
        """Place a new order."""
        order_id = self._generate_order_id()
        
        order = Order(
            order_id=order_id,
            exchange_id=exchange_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            stop_price=stop_price,
            status=OrderStatus.PENDING,
            strategy=strategy,
            agent_id=agent_id,
            notes=notes
        )
        
        self._orders[order_id] = order
        
        if self.paper_trading:
            # Paper trading - simulate execution
            await self._simulate_order(order)
        else:
            # Live trading
            await self._execute_order(order)
        
        return order
    
    async def _simulate_order(self, order: Order) -> None:
        """Simulate order execution for paper trading."""
        await asyncio.sleep(0.1)  # Simulate latency
        
        # Get current price from exchange
        conn = self.exchange_manager.get_connection(order.exchange_id)
        current_price = 0
        
        if conn and conn.is_connected:
            ticker = await conn.fetch_ticker(order.symbol)
            if ticker:
                current_price = ticker.get('last', order.price or 0)
        else:
            current_price = order.price or 100  # Fallback
        
        order.status = OrderStatus.FILLED
        order.filled_amount = order.amount
        order.avg_fill_price = current_price
        order.filled_at = datetime.now()
        order.updated_at = datetime.now()
        
        # Create trade record
        trade = Trade(
            trade_id=f"TRD-{order.order_id}",
            order_id=order.order_id,
            exchange_id=order.exchange_id,
            symbol=order.symbol,
            side=order.side,
            amount=order.amount,
            price=current_price,
            fee=current_price * order.amount * 0.001,  # 0.1% fee
            fee_currency="USDT",
            executed_at=datetime.now(),
            strategy=order.strategy,
            agent_id=order.agent_id
        )
        self._trades.append(trade)
        
        # Update position
        self._update_position_from_trade(order, current_price)
        
        logger.info(f"Paper order filled: {order.order_id} {order.side.value} {order.amount} {order.symbol} @ {current_price}")
    
    async def _execute_order(self, order: Order) -> None:
        """Execute order on live exchange."""
        conn = self.exchange_manager.get_connection(order.exchange_id)
        
        if not conn or not conn.is_connected:
            order.status = OrderStatus.REJECTED
            order.notes = "Exchange not connected"
            logger.error(f"Order rejected: {order.exchange_id} not connected")
            return
        
        try:
            order.status = OrderStatus.OPEN
            
            # Place order via CCXT
            if order.order_type == OrderType.MARKET:
                result = await conn.place_order_async(
                    symbol=order.symbol,
                    type='market',
                    side=order.side.value,
                    amount=order.amount
                )
            elif order.order_type == OrderType.LIMIT:
                result = await conn.place_order_async(
                    symbol=order.symbol,
                    type='limit',
                    side=order.side.value,
                    amount=order.amount,
                    price=order.price
                )
            else:
                result = None
            
            if result:
                order.order_id = result.get('id', order.order_id)
                order.status = OrderStatus.FILLED if result.get('status') == 'closed' else OrderStatus.OPEN
                order.filled_amount = result.get('filled', order.amount)
                order.avg_fill_price = result.get('average', order.price or 0)
                
                if order.status == OrderStatus.FILLED:
                    order.filled_at = datetime.now()
                    self._update_position_from_trade(order, order.avg_fill_price)
                
                logger.info(f"Order executed: {order.order_id} on {order.exchange_id}")
            else:
                order.status = OrderStatus.FAILED
                order.notes = "No response from exchange"
                
        except Exception as e:
            order.status = OrderStatus.FAILED
            order.notes = str(e)
            logger.error(f"Order execution failed: {e}")
    
    def _update_position_from_trade(self, order: Order, price: float) -> None:
        """Update position based on filled order."""
        pos_key = f"{order.exchange_id}:{order.symbol}"
        
        if order.side == OrderSide.BUY:
            if pos_key in self._positions:
                pos = self._positions[pos_key]
                # Add to position
                total_amount = pos.amount + order.amount
                pos.entry_price = (pos.entry_price * pos.amount + price * order.amount) / total_amount
                pos.amount = total_amount
                pos.current_price = price
                pos.unrealized_pnl = (price - pos.entry_price) * pos.amount
                pos.pnl_pct = (price / pos.entry_price - 1) * 100 if pos.entry_price > 0 else 0
                pos.orders.append(order.order_id)
                pos.updated_at = datetime.now()
            else:
                # Create new position
                self._positions[pos_key] = Position(
                    position_id=f"POS-{pos_key.replace(':', '-')}",
                    exchange_id=order.exchange_id,
                    symbol=order.symbol,
                    side=OrderSide.BUY,
                    amount=order.amount,
                    entry_price=price,
                    current_price=price,
                    unrealized_pnl=(price - price) * order.amount,  # = 0 for new
                    orders=[order.order_id],
                    strategy=order.strategy,
                    agent_id=order.agent_id
                )
        else:  # SELL - close position
            if pos_key in self._positions:
                pos = self._positions[pos_key]
                realized_pnl = (price - pos.entry_price) * min(order.amount, pos.amount)
                
                # Record trade P&L
                pos.pnl += realized_pnl
                pos.amount -= order.amount
                pos.updated_at = datetime.now()
                
                if pos.amount <= 0:
                    del self._positions[pos_key]
            # If no position, short selling would create new position (not implemented)
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        if order_id not in self._orders:
            return False
        
        order = self._orders[order_id]
        
        if order.status not in [OrderStatus.PENDING, OrderStatus.OPEN]:
            return False
        
        if self.paper_trading:
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            return True
        
        # Live cancellation
        conn = self.exchange_manager.get_connection(order.exchange_id)
        if conn and conn.is_connected:
            success = await conn.cancel_order(order.order_id, order.symbol)
            if success:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()
            return success
        
        return False
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self._orders.get(order_id)
    
    def get_open_orders(self) -> List[Order]:
        """Get all open orders."""
        return [o for o in self._orders.values() if o.status == OrderStatus.OPEN]
    
    def get_position(self, exchange_id: str, symbol: str) -> Optional[Position]:
        """Get position for exchange and symbol."""
        pos_key = f"{exchange_id}:{symbol}"
        return self._positions.get(pos_key)
    
    def get_all_positions(self) -> List[Position]:
        """Get all open positions."""
        return list(self._positions.values())
    
    def get_trades(self, limit: int = 100) -> List[Trade]:
        """Get recent trades."""
        return sorted(self._trades, key=lambda t: t.executed_at, reverse=True)[:limit]
    
    async def update_positions(self) -> None:
        """Update current prices and P&L for all positions."""
        for pos in self._positions.values():
            conn = self.exchange_manager.get_connection(pos.exchange_id)
            
            if conn and conn.is_connected:
                ticker = await conn.fetch_ticker(pos.symbol)
                if ticker:
                    pos.current_price = ticker.get('last', pos.current_price)
                    pos.unrealized_pnl = (pos.current_price - pos.entry_price) * pos.amount
                    pos.pnl_pct = (pos.current_price / pos.entry_price - 1) * 100 if pos.entry_price > 0 else 0
                    pos.updated_at = datetime.now()
    
    def get_total_pnl(self) -> Dict[str, float]:
        """Calculate total P&L."""
        realized_pnl = sum(p.pnl for p in self._positions.values())
        unrealized_pnl = sum(p.unrealized_pnl for p in self._positions.values())
        
        return {
            "realized": realized_pnl,
            "unrealized": unrealized_pnl,
            "total": realized_pnl + unrealized_pnl
        }
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary."""
        positions = self.get_all_positions()
        
        total_value = 0
        total_pnl = 0
        
        for pos in positions:
            value = pos.amount * pos.current_price
            total_value += value
            total_pnl += pos.pnl + pos.unrealized_pnl
        
        return {
            "total_value": total_value,
            "total_pnl": total_pnl,
            "position_count": len(positions),
            "open_orders": len(self.get_open_orders()),
            "trades_today": len([t for t in self._trades if t.executed_at.date() == datetime.now().date()])
        }


class TradeHistory:
    """Manages trade history and analytics."""
    
    def __init__(self):
        self._trades: List[Trade] = []
        self._daily_pnl: Dict[str, float] = {}
    
    def add_trade(self, trade: Trade) -> None:
        """Add a trade to history."""
        self._trades.append(trade)
        date_key = trade.executed_at.strftime('%Y-%m-%d')
        
        if date_key not in self._daily_pnl:
            self._daily_pnl[date_key] = 0
        
        pnl = trade.price * trade.amount if trade.side == OrderSide.BUY else -trade.price * trade.amount
        self._daily_pnl[date_key] += pnl - trade.fee
    
    def get_trades(
        self,
        exchange_id: str = None,
        symbol: str = None,
        strategy: str = None,
        limit: int = 100
    ) -> List[Trade]:
        """Get filtered trades."""
        filtered = self._trades
        
        if exchange_id:
            filtered = [t for t in filtered if t.exchange_id == exchange_id]
        if symbol:
            filtered = [t for t in filtered if t.symbol == symbol]
        if strategy:
            filtered = [t for t in filtered if t.strategy == strategy]
        
        return sorted(filtered, key=lambda t: t.executed_at, reverse=True)[:limit]
    
    def get_win_rate(self, symbol: str = None) -> float:
        """Calculate win rate."""
        trades = self.get_trades(symbol=symbol, limit=1000)
        
        if not trades:
            return 0
        
        wins = 0
        total = 0
        
        # Group by order to determine win/loss
        order_trades: Dict[str, List[Trade]] = {}
        for trade in trades:
            if trade.order_id not in order_trades:
                order_trades[trade.order_id] = []
            order_trades[trade.order_id].append(trade)
        
        for order_id, order_trade_list in order_trades.items():
            if len(order_trade_list) >= 2:  # Entry and exit
                entry = next((t for t in order_trade_list if t.side == OrderSide.BUY), None)
                exit_trade = next((t for t in order_trade_list if t.side == OrderSide.SELL), None)
                
                if entry and exit_trade:
                    pnl = (exit_trade.price - entry.price) * entry.amount - entry.fee - exit_trade.fee
                    if pnl > 0:
                        wins += 1
                    total += 1
        
        return wins / total * 100 if total > 0 else 0
    
    def get_pnl_history(self, days: int = 30) -> Dict[str, float]:
        """Get daily P&L for the last N days."""
        result = {}
        today = datetime.now().date()
        
        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            result[date] = self._daily_pnl.get(date, 0)
        
        return result
