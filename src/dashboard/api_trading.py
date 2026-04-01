"""
KEOTrading Trading API
=====================
API endpoints for trading agents and portfolio management.

Based on agent-team-orchestration skill.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from src.agents.trading_agents import (
    get_trading_orchestrator,
    TaskStatus,
)
from src.portfolio.tracker import get_portfolio_tracker

router = APIRouter(prefix="/trading", tags=["Trading"])


# -------------------------------------------------------------------
# Pydantic Models
# -------------------------------------------------------------------

class TradeSignalRequest(BaseModel):
    """Request to create a trade signal."""
    model_config = ConfigDict(from_attributes=True)
    
    symbol: str = Field(..., description="Trading pair, e.g. BTC/USDT")
    action: str = Field(..., description="buy or sell")
    price: float = Field(..., description="Entry price")
    quantity: float = Field(0.1, description="Position size")


class TaskResponse(BaseModel):
    """Task response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    type: str
    description: str
    status: str
    priority: int
    assigned_to: Optional[str] = None


class AgentStatusResponse(BaseModel):
    """Agent status response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    role: str
    status: str
    capabilities: List[str]
    current_task: Optional[str] = None


class PortfolioMetricsResponse(BaseModel):
    """Portfolio metrics response."""
    model_config = ConfigDict(from_attributes=True)
    
    current_equity: float
    cash: float
    position_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_return_pct: float
    trade_count: int
    win_rate: float
    max_drawdown: float


# -------------------------------------------------------------------
# Trading Agent Endpoints
# -------------------------------------------------------------------

@router.get("/agents", response_model=List[AgentStatusResponse])
async def list_trading_agents() -> List[AgentStatusResponse]:
    """List all trading agents and their status."""
    orchestrator = get_trading_orchestrator()
    agents = orchestrator.get_agent_status()
    return [
        AgentStatusResponse(
            id=a["id"],
            name=a["name"],
            role=a["role"],
            status=a["status"],
            capabilities=a["capabilities"],
            current_task=a.get("current_task"),
        )
        for a in agents
    ]


@router.get("/agents/{agent_id}", response_model=AgentStatusResponse)
async def get_trading_agent(agent_id: str) -> AgentStatusResponse:
    """Get a specific trading agent."""
    orchestrator = get_trading_orchestrator()
    agents = orchestrator.get_agent_status()
    
    for a in agents:
        if a["id"] == agent_id:
            return AgentStatusResponse(
                id=a["id"],
                name=a["name"],
                role=a["role"],
                status=a["status"],
                capabilities=a["capabilities"],
                current_task=a.get("current_task"),
            )
    
    raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")


@router.get("/tasks")
async def get_task_board() -> Dict[str, Any]:
    """Get task board with all tasks."""
    orchestrator = get_trading_orchestrator()
    return orchestrator.get_task_board()


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """Get a specific task."""
    orchestrator = get_trading_orchestrator()
    task = orchestrator.tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    
    return TaskResponse(
        id=task.id,
        type=task.type,
        description=task.description,
        status=task.status.value,
        priority=task.priority,
        assigned_to=task.assigned_to,
    )


@router.post("/tasks/{task_id}/run")
async def run_task(task_id: str) -> Dict[str, Any]:
    """Run a specific task."""
    orchestrator = get_trading_orchestrator()
    return await orchestrator.run_task(task_id)


@router.post("/signal")
async def create_trade_signal(request: TradeSignalRequest) -> Dict[str, Any]:
    """
    Create a complete trading workflow:
    1. Signal Analysis
    2. Risk Check  
    3. Order Execution
    
    Returns the signal analysis task ID.
    """
    orchestrator = get_trading_orchestrator()
    
    signal_task_id = orchestrator.create_trade_signal(
        symbol=request.symbol,
        action=request.action,
        price=request.price,
        quantity=request.quantity,
    )
    
    return {
        "workflow_started": True,
        "signal_task_id": signal_task_id,
        "symbol": request.symbol,
        "action": request.action,
    }


# -------------------------------------------------------------------
# Portfolio Endpoints
# -------------------------------------------------------------------

@router.get("/portfolio/metrics", response_model=PortfolioMetricsResponse)
async def get_portfolio_metrics() -> PortfolioMetricsResponse:
    """Get portfolio metrics."""
    tracker = get_portfolio_tracker()
    metrics = tracker.metrics
    
    return PortfolioMetricsResponse(
        current_equity=metrics.current_equity,
        cash=metrics.cash,
        position_value=metrics.position_value,
        unrealized_pnl=metrics.unrealized_pnl,
        realized_pnl=metrics.realized_pnl,
        total_return_pct=metrics.total_return_pct,
        trade_count=metrics.trade_count,
        win_rate=metrics.win_rate,
        max_drawdown=metrics.max_drawdown,
    )


@router.get("/portfolio/positions")
async def get_positions() -> List[Dict[str, Any]]:
    """Get current positions."""
    tracker = get_portfolio_tracker()
    return [
        {
            "symbol": p.symbol,
            "name": p.name,
            "quantity": p.quantity,
            "cost": p.cost,
            "current_price": p.current_price,
            "network": p.network,
            "source": p.source,
            "unrealized_pnl": (p.current_price - p.cost) * p.quantity,
        }
        for p in tracker.positions
    ]


@router.get("/portfolio/equity-curve")
async def get_equity_curve() -> List[Dict[str, Any]]:
    """Get equity curve history."""
    tracker = get_portfolio_tracker()
    return tracker.equity_curve


@router.post("/portfolio/positions")
async def add_position(data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new position."""
    from src.portfolio.tracker import Position
    
    tracker = get_portfolio_tracker()
    
    position = Position(
        symbol=data["symbol"],
        name=data.get("name", data["symbol"]),
        quantity=data["quantity"],
        cost=data["cost"],
        network=data.get("network", "ethereum"),
        source=data.get("source", ""),
    )
    
    tracker.add_position(position)
    
    return {
        "success": True,
        "symbol": position.symbol,
        "quantity": position.quantity,
    }


@router.delete("/portfolio/positions/{symbol}")
async def remove_position(symbol: str) -> Dict[str, Any]:
    """Remove a position."""
    tracker = get_portfolio_tracker()
    tracker.remove_position(symbol)
    
    return {"success": True, "symbol": symbol}


@router.post("/portfolio/prices/refresh")
async def refresh_prices() -> Dict[str, Any]:
    """Refresh prices from CoinGecko."""
    tracker = get_portfolio_tracker()
    prices = await tracker.fetch_prices_from_coingecko()
    await tracker.update_prices(prices)
    
    return {
        "success": True,
        "prices_updated": len(prices),
        "prices": prices,
    }
