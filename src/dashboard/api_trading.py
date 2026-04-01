"""
Order Execution API Endpoints
REST API for order placement, position management, and trade history.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# -------------------------------------------------------------------
# Enums
# -------------------------------------------------------------------

class OrderSideEnum(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderTypeEnum(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"


# -------------------------------------------------------------------
# Request Models
# -------------------------------------------------------------------

class PlaceOrderRequest(BaseModel):
    exchange_id: str = Field(..., description="Exchange ID (e.g., binance, kraken)")
    symbol: str = Field(..., description="Trading pair (e.g., BTC/USDT)")
    side: OrderSideEnum = Field(..., description="Order side: buy or sell")
    order_type: OrderTypeEnum = Field(default=OrderTypeEnum.MARKET, description="Order type")
    amount: float = Field(..., gt=0, description="Order amount")
    price: Optional[float] = Field(None, gt=0, description="Limit price (required for limit orders)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price (for stop orders)")
    strategy: str = Field(default="manual", description="Strategy name")
    agent_id: str = Field(default="", description="Agent ID")
    notes: str = Field(default="", description="Order notes")


class CancelOrderRequest(BaseModel):
    order_id: str = Field(..., description="Order ID to cancel")


class SetStopLossRequest(BaseModel):
    position_id: str = Field(..., description="Position ID")
    stop_loss_price: float = Field(..., gt=0, description="Stop loss price")


class SetTakeProfitRequest(BaseModel):
    position_id: str = Field(..., description="Position ID")
    take_profit_price: float = Field(..., gt=0, description="Take profit price")


class ClosePositionRequest(BaseModel):
    position_id: str = Field(..., description="Position ID to close")
    amount: Optional[float] = Field(None, gt=0, description="Amount to close (optional, closes full if not specified)")


# -------------------------------------------------------------------
# Response Models
# -------------------------------------------------------------------

class OrderResponse(BaseModel):
    order_id: str
    exchange_id: str
    symbol: str
    side: str
    order_type: str
    amount: float
    price: Optional[float]
    filled_amount: float
    avg_fill_price: float
    status: str
    created_at: str
    filled_at: Optional[str]
    fee: float
    strategy: str
    agent_id: str


class PositionResponse(BaseModel):
    position_id: str
    exchange_id: str
    symbol: str
    side: str
    amount: float
    entry_price: float
    current_price: float
    pnl: float
    pnl_pct: float
    unrealized_pnl: float
    opened_at: str
    stop_loss: Optional[float]
    take_profit: Optional[float]
    strategy: str


class TradeResponse(BaseModel):
    trade_id: str
    order_id: str
    exchange_id: str
    symbol: str
    side: str
    amount: float
    price: float
    fee: float
    executed_at: str
    strategy: str


class PortfolioSummaryResponse(BaseModel):
    total_value: float
    total_pnl: float
    position_count: int
    open_orders: int
    trades_today: int


# -------------------------------------------------------------------
# Mock order executor for demo (replace with real implementation)
# -------------------------------------------------------------------

# In-memory mock data for demo
_mock_orders: Dict[str, Any] = {}
_mock_positions: Dict[str, Any] = {}
_mock_trades: List[Dict] = []
_order_counter = 0


def _generate_order_id() -> str:
    global _order_counter
    _order_counter += 1
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{_order_counter:06d}"


def _generate_position_id() -> str:
    return f"POS-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


# -------------------------------------------------------------------
# Router
# -------------------------------------------------------------------

router = APIRouter(prefix="/trading", tags=["Trading"])


@router.post("/orders", response_model=OrderResponse)
async def place_order(request: PlaceOrderRequest) -> OrderResponse:
    """
    Place a new order.
    
    - **exchange_id**: Exchange to trade on (binance, kraken, bybit, coinbase)
    - **symbol**: Trading pair (BTC/USDT, ETH/USDT, etc.)
    - **side**: BUY or SELL
    - **order_type**: MARKET, LIMIT, STOP_LOSS, STOP_LIMIT
    - **amount**: Order amount
    - **price**: Limit price (required for LIMIT orders)
    """
    # Generate order
    order_id = _generate_order_id()
    
    order = {
        "order_id": order_id,
        "exchange_id": request.exchange_id,
        "symbol": request.symbol,
        "side": request.side.value,
        "order_type": request.order_type.value,
        "amount": request.amount,
        "price": request.price,
        "filled_amount": 0,
        "avg_fill_price": 0,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "filled_at": None,
        "fee": 0,
        "strategy": request.strategy,
        "agent_id": request.agent_id,
    }
    
    _mock_orders[order_id] = order
    
    # Simulate immediate fill for market orders
    if request.order_type == OrderTypeEnum.MARKET:
        order["status"] = "filled"
        order["filled_amount"] = request.amount
        order["avg_fill_price"] = request.price or 64000  # Mock price
        order["filled_at"] = datetime.now().isoformat()
        order["fee"] = order["filled_amount"] * order["avg_fill_price"] * 0.001
        
        # Create mock position
        pos_id = _generate_position_id()
        position = {
            "position_id": pos_id,
            "exchange_id": request.exchange_id,
            "symbol": request.symbol,
            "side": request.side.value,
            "amount": request.amount,
            "entry_price": order["avg_fill_price"],
            "current_price": order["avg_fill_price"],
            "pnl": 0,
            "pnl_pct": 0,
            "unrealized_pnl": 0,
            "opened_at": datetime.now().isoformat(),
            "stop_loss": None,
            "take_profit": None,
            "strategy": request.strategy,
        }
        _mock_positions[pos_id] = position
        
        # Create mock trade
        trade = {
            "trade_id": f"TRD-{order_id}",
            "order_id": order_id,
            "exchange_id": request.exchange_id,
            "symbol": request.symbol,
            "side": request.side.value,
            "amount": request.amount,
            "price": order["avg_fill_price"],
            "fee": order["fee"],
            "executed_at": datetime.now().isoformat(),
            "strategy": request.strategy,
        }
        _mock_trades.append(trade)
    
    return OrderResponse(**order)


@router.get("/orders")
async def list_orders(
    status: Optional[str] = None,
    exchange_id: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 50
) -> List[OrderResponse]:
    """
    List orders with optional filtering.
    
    - **status**: Filter by status (pending, open, filled, cancelled)
    - **exchange_id**: Filter by exchange
    - **symbol**: Filter by trading pair
    - **limit**: Maximum number of orders to return
    """
    orders = list(_mock_orders.values())
    
    if status:
        orders = [o for o in orders if o["status"] == status]
    if exchange_id:
        orders = [o for o in orders if o["exchange_id"] == exchange_id]
    if symbol:
        orders = [o for o in orders if o["symbol"] == symbol]
    
    # Sort by creation time, newest first
    orders.sort(key=lambda x: x["created_at"], reverse=True)
    
    return [OrderResponse(**o) for o in orders[:limit]]


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str) -> OrderResponse:
    """Get a specific order by ID."""
    if order_id not in _mock_orders:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    return OrderResponse(**_mock_orders[order_id])


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str) -> Dict[str, Any]:
    """Cancel an open order."""
    if order_id not in _mock_orders:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")
    
    order = _mock_orders[order_id]
    
    if order["status"] not in ["pending", "open"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status '{order['status']}'"
        )
    
    order["status"] = "cancelled"
    order["updated_at"] = datetime.now().isoformat()
    
    return {"success": True, "order_id": order_id, "status": "cancelled"}


@router.get("/positions")
async def list_positions(
    exchange_id: Optional[str] = None,
    symbol: Optional[str] = None,
) -> List[PositionResponse]:
    """
    List open positions.
    
    - **exchange_id**: Filter by exchange
    - **symbol**: Filter by trading pair
    """
    positions = list(_mock_positions.values())
    
    if exchange_id:
        positions = [p for p in positions if p["exchange_id"] == exchange_id]
    if symbol:
        positions = [p for p in positions if p["symbol"] == symbol]
    
    return [PositionResponse(**p) for p in positions]


@router.get("/positions/{position_id}", response_model=PositionResponse)
async def get_position(position_id: str) -> PositionResponse:
    """Get a specific position by ID."""
    if position_id not in _mock_positions:
        raise HTTPException(status_code=404, detail=f"Position '{position_id}' not found")
    return PositionResponse(**_mock_positions[position_id])


@router.post("/positions/{position_id}/stop-loss")
async def set_stop_loss(position_id: str, request: SetStopLossRequest) -> Dict[str, Any]:
    """Set or update stop loss for a position."""
    if position_id not in _mock_positions:
        raise HTTPException(status_code=404, detail=f"Position '{position_id}' not found")
    
    position = _mock_positions[position_id]
    position["stop_loss"] = request.stop_loss_price
    
    return {
        "success": True,
        "position_id": position_id,
        "stop_loss": request.stop_loss_price
    }


@router.post("/positions/{position_id}/take-profit")
async def set_take_profit(position_id: str, request: SetTakeProfitRequest) -> Dict[str, Any]:
    """Set or update take profit for a position."""
    if position_id not in _mock_positions:
        raise HTTPException(status_code=404, detail=f"Position '{position_id}' not found")
    
    position = _mock_positions[position_id]
    position["take_profit"] = request.take_profit_price
    
    return {
        "success": True,
        "position_id": position_id,
        "take_profit": request.take_profit_price
    }


@router.post("/positions/{position_id}/close")
async def close_position(position_id: str, request: ClosePositionRequest) -> Dict[str, Any]:
    """Close a position (full or partial)."""
    if position_id not in _mock_positions:
        raise HTTPException(status_code=404, detail=f"Position '{position_id}' not found")
    
    position = _mock_positions[position_id]
    
    close_amount = request.amount or position["amount"]
    
    if close_amount > position["amount"]:
        raise HTTPException(
            status_code=400,
            detail=f"Close amount ({close_amount}) exceeds position size ({position['amount']})"
        )
    
    # Calculate P&L
    pnl = (position["current_price"] - position["entry_price"]) * close_amount
    if position["side"] == "sell":
        pnl = -pnl
    
    # Create closing trade
    trade = {
        "trade_id": f"TRD-CLOSE-{position_id}",
        "order_id": f"ORD-CLOSE-{position_id}",
        "exchange_id": position["exchange_id"],
        "symbol": position["symbol"],
        "side": "sell" if position["side"] == "buy" else "buy",
        "amount": close_amount,
        "price": position["current_price"],
        "fee": position["current_price"] * close_amount * 0.001,
        "executed_at": datetime.now().isoformat(),
        "strategy": position["strategy"],
    }
    _mock_trades.append(trade)
    
    # Update position
    if close_amount >= position["amount"]:
        # Full close
        del _mock_positions[position_id]
    else:
        # Partial close
        position["amount"] -= close_amount
        position["pnl"] += pnl
    
    return {
        "success": True,
        "position_id": position_id,
        "closed_amount": close_amount,
        "pnl": pnl
    }


@router.get("/trades")
async def list_trades(
    exchange_id: Optional[str] = None,
    symbol: Optional[str] = None,
    strategy: Optional[str] = None,
    limit: int = 100
) -> List[TradeResponse]:
    """
    List executed trades.
    
    - **exchange_id**: Filter by exchange
    - **symbol**: Filter by trading pair
    - **strategy**: Filter by strategy
    - **limit**: Maximum number of trades to return
    """
    trades = list(_mock_trades)
    
    if exchange_id:
        trades = [t for t in trades if t["exchange_id"] == exchange_id]
    if symbol:
        trades = [t for t in trades if t["symbol"] == symbol]
    if strategy:
        trades = [t for t in trades if t["strategy"] == strategy]
    
    trades.sort(key=lambda x: x["executed_at"], reverse=True)
    
    return [TradeResponse(**t) for t in trades[:limit]]


@router.get("/portfolio/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary() -> PortfolioSummaryResponse:
    """Get portfolio summary with P&L and statistics."""
    total_value = sum(
        p["amount"] * p["current_price"] 
        for p in _mock_positions.values()
    )
    total_pnl = sum(
        p["pnl"] + p["unrealized_pnl"] 
        for p in _mock_positions.values()
    )
    
    trades_today = len([
        t for t in _mock_trades 
        if t["executed_at"].startswith(datetime.now().strftime("%Y-%m-%d"))
    ])
    
    return PortfolioSummaryResponse(
        total_value=total_value,
        total_pnl=total_pnl,
        position_count=len(_mock_positions),
        open_orders=len([o for o in _mock_orders.values() if o["status"] == "open"]),
        trades_today=trades_today
    )


# Need to import uuid
import uuid
