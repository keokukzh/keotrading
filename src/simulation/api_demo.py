"""
KEOTrading Demo Trading API
==========================
API endpoints for demo trading with virtual portfolio.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from src.simulation.portfolio import get_virtual_portfolio, VirtualPortfolio
from src.simulation.engine import get_simulation_engine, SimulationEngine
from src.simulation.agents import get_demo_agents, DemoTradingAgents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["Demo Trading"])


# -------------------------------------------------------------------
# Pydantic Models
# -------------------------------------------------------------------

class OrderRequest(BaseModel):
    """Request to create a demo order."""
    model_config = ConfigDict(from_attributes=True)
    
    symbol: str = Field(..., description="Trading pair, e.g. BTC/USDT")
    side: str = Field(..., description="buy or sell")
    order_type: str = Field("market", description="market or limit")
    quantity: float = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(None, description="Limit price (for limit orders)")


class ResetRequest(BaseModel):
    """Request to reset demo portfolio."""
    initial_balance: float = Field(100_000, description="Initial balance in USD")


class AgentStartRequest(BaseModel):
    """Request to start a demo agent."""
    agent_id: str = Field(..., description="Agent ID to start")


# -------------------------------------------------------------------
# Portfolio Endpoints
# -------------------------------------------------------------------

@router.get("/portfolio")
async def get_demo_portfolio() -> Dict[str, Any]:
    """Get current demo portfolio state."""
    portfolio = get_virtual_portfolio()
    return portfolio.get_summary()


@router.post("/portfolio/reset")
async def reset_demo_portfolio(request: ResetRequest) -> Dict[str, Any]:
    """Reset demo portfolio to initial state."""
    portfolio = get_virtual_portfolio()
    portfolio.reset(initial_balance=request.initial_balance)
    
    return {
        "success": True,
        "initial_balance": request.initial_balance,
        "message": f"Portfolio reset to ${request.initial_balance:,.2f}",
    }


@router.get("/portfolio/prices")
async def get_demo_prices() -> Dict[str, Any]:
    """Get current prices for demo trading."""
    engine = get_simulation_engine()
    prices = await engine.fetch_prices()
    
    return {
        "prices": {
            symbol: {
                "last": p.last,
                "bid": p.bid,
                "ask": p.ask,
                "spread": p.spread,
                "source": p.source,
            }
            for symbol, p in prices.items()
        },
        "timestamp": datetime.now().isoformat(),
    }


# -------------------------------------------------------------------
# Order Endpoints
# -------------------------------------------------------------------

@router.get("/orders")
async def list_demo_orders(
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List demo orders."""
    portfolio = get_virtual_portfolio()
    orders = portfolio.orders[-limit:]
    
    if status:
        orders = [o for o in orders if o.status == status]
    
    return [o.to_dict() for o in orders]


@router.post("/orders")
async def create_demo_order(request: OrderRequest) -> Dict[str, Any]:
    """Create and execute a demo order."""
    engine = get_simulation_engine()
    portfolio = get_virtual_portfolio()
    
    # Set portfolio on engine
    engine.set_portfolio(portfolio)
    
    # Create order
    order_data = {
        "symbol": request.symbol,
        "side": request.side,
        "order_type": request.order_type,
        "quantity": request.quantity,
        "price": request.price or 0,
    }
    
    # Execute order
    result = await engine.run_order_simulation(order_data)
    
    return result


@router.delete("/orders/{order_id}")
async def cancel_demo_order(order_id: str) -> Dict[str, Any]:
    """Cancel a pending demo order."""
    portfolio = get_virtual_portfolio()
    success = portfolio.cancel_order(order_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Order not found or not pending")
    
    return {"success": True, "order_id": order_id}


# -------------------------------------------------------------------
# Metrics Endpoints
# -------------------------------------------------------------------

@router.get("/metrics")
async def get_demo_metrics() -> Dict[str, Any]:
    """Get demo trading metrics."""
    portfolio = get_virtual_portfolio()
    metrics = portfolio.metrics
    
    return {
        "initial_balance": metrics.initial_balance,
        "current_equity": metrics.current_equity,
        "cash": metrics.cash,
        "position_value": metrics.position_value,
        "unrealized_pnl": metrics.unrealized_pnl,
        "realized_pnl": metrics.realized_pnl,
        "total_pnl": metrics.total_pnl,
        "total_return_pct": metrics.total_return_pct,
        "trade_count": metrics.trade_count,
        "win_count": metrics.win_count,
        "loss_count": metrics.loss_count,
        "win_rate": metrics.win_rate,
        "max_drawdown": metrics.max_drawdown,
        "sharpe_ratio": metrics.sharpe_ratio,
        "avg_trade_pnl": metrics.avg_trade_pnl,
    }


@router.get("/equity-curve")
async def get_demo_equity_curve(limit: int = 100) -> List[Dict[str, Any]]:
    """Get equity curve history."""
    portfolio = get_virtual_portfolio()
    return portfolio.equity_curve[-limit:]


# -------------------------------------------------------------------
# Demo Agents Endpoints
# -------------------------------------------------------------------

@router.get("/agents")
async def list_demo_agents() -> List[Dict[str, Any]]:
    """List all demo trading agents."""
    agents = get_demo_agents()
    
    # Connect to portfolio and engine
    portfolio = get_virtual_portfolio()
    engine = get_simulation_engine()
    agents.set_portfolio(portfolio)
    agents.set_engine(engine)
    
    return agents.get_agent_status()


@router.post("/agents/{agent_id}/start")
async def start_demo_agent(agent_id: str) -> Dict[str, Any]:
    """Start a demo trading agent."""
    agents = get_demo_agents()
    
    # Connect to portfolio and engine
    portfolio = get_virtual_portfolio()
    engine = get_simulation_engine()
    agents.set_portfolio(portfolio)
    agents.set_engine(engine)
    
    success = await agents.start_agent(agent_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    return {
        "success": True,
        "agent_id": agent_id,
        "status": "running",
    }


@router.post("/agents/{agent_id}/stop")
async def stop_demo_agent(agent_id: str) -> Dict[str, Any]:
    """Stop a demo trading agent."""
    agents = get_demo_agents()
    success = await agents.stop_agent(agent_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    return {
        "success": True,
        "agent_id": agent_id,
        "status": "stopped",
    }


@router.post("/agents/{agent_id}/signal")
async def trigger_demo_agent_signal(
    agent_id: str,
    symbol: str = "BTC/USDT",
) -> Dict[str, Any]:
    """Manually trigger a signal from a demo agent."""
    agents = get_demo_agents()
    engine = get_simulation_engine()
    portfolio = get_virtual_portfolio()
    
    agents.set_portfolio(portfolio)
    agents.set_engine(engine)
    
    agent = agents.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    # Get current price
    await engine.fetch_prices()
    price_data = engine.prices.get(symbol)
    if not price_data:
        raise HTTPException(status_code=400, detail=f"No price for {symbol}")
    
    # Generate signal based on agent strategy
    from src.simulation.agents import StrategyType
    
    if agent.strategy == StrategyType.MEAN_REVERSION:
        signal = await agents.generate_mean_reversion_signal(symbol, price_data.last)
    elif agent.strategy == StrategyType.MOMENTUM:
        signal = await agents.generate_momentum_signal(symbol, price_data.last)
    else:
        return {"error": "Grid signals are generated automatically"}
    
    if signal:
        # Execute signal
        await agents._execute_signal(signal)
        return {
            "signal": {
                "id": signal.id,
                "symbol": signal.symbol,
                "side": signal.side,
                "quantity": signal.quantity,
                "entry_price": signal.entry_price,
                "confidence": signal.confidence,
                "reason": signal.reason,
                "executed": signal.executed,
            }
        }
    
    return {"message": "No signal generated", "reason": "Market conditions not met"}


# -------------------------------------------------------------------
# Trade Signal Endpoint (Convenience)
# -------------------------------------------------------------------

@router.post("/signal")
async def create_demo_signal(request: OrderRequest) -> Dict[str, Any]:
    """
    Create a demo trade signal.
    Convenience endpoint that generates a signal and executes it.
    """
    engine = get_simulation_engine()
    portfolio = get_virtual_portfolio()
    agents = get_demo_agents()
    
    engine.set_portfolio(portfolio)
    agents.set_portfolio(portfolio)
    agents.set_engine(engine)
    
    # Create order
    result = await create_demo_order(request)
    
    return {
        "success": result.get("success", False),
        "order": result,
        "message": f"Demo {request.side} order for {request.quantity} {request.symbol}",
    }
