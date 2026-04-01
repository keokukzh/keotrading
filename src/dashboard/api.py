"""
KEOTrading Dashboard - FastAPI Backend
========================================
REST API for agent management, portfolio, strategies, and P&L tracking.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import random


# -------------------------------------------------------------------
# Pydantic Models
# -------------------------------------------------------------------

class AgentStatus(BaseModel):
    id: str
    name: str
    strategy: str
    status: str  # running, paused, stopped, error
    pnl: float = 0.0
    pnl_24h: float = 0.0
    trades: int = 0
    win_rate: float = 0.0
    uptime: str = ""
    last_trade: str = ""
    memory_mb: int = 0
    cpu_pct: float = 0.0
    errors: int = 0


class AgentAction(BaseModel):
    agent_id: str
    action: str  # start, stop, restart, pause


class Strategy(BaseModel):
    name: str
    description: str
    risk: str
    expected_return: str
    best_for: str
    stars: int = 3
    tags: List[str] = []


class StrategySelection(BaseModel):
    strategy_name: str
    agent_id: Optional[str] = None


class PortfolioPosition(BaseModel):
    asset: str
    amount: float
    value_usd: float
    allocation: float
    source: str


class Portfolio(BaseModel):
    total_value_usd: float
    positions: List[PortfolioPosition]
    last_updated: str


class PnLEntry(BaseModel):
    date: str
    pnl: float
    pnl_cumulative: float


# -------------------------------------------------------------------
# Mock Data Store
# -------------------------------------------------------------------

AGENTS_DB: Dict[str, AgentStatus] = {
    "agent-001": AgentStatus(
        id="agent-001", name="Hzjken LP Agent", strategy="LP Arbitrage",
        status="running", pnl=4521.30, pnl_24h=234.50, trades=1247,
        win_rate=72.4, uptime="6d 14h 22m", last_trade="2 min ago",
        memory_mb=512, cpu_pct=12.5, errors=0,
    ),
    "agent-002": AgentStatus(
        id="agent-002", name="Scalper Alpha", strategy="Scalping",
        status="running", pnl=2134.80, pnl_24h=87.20, trades=3421,
        win_rate=61.8, uptime="3d 2h 15m", last_trade="30 sec ago",
        memory_mb=384, cpu_pct=18.3, errors=2,
    ),
    "agent-003": AgentStatus(
        id="agent-003", name="Grid Bot Beta", strategy="Grid Trading",
        status="paused", pnl=-234.50, pnl_24h=-12.30, trades=156,
        win_rate=54.2, uptime="2d 8h 05m", last_trade="4h ago",
        memory_mb=256, cpu_pct=3.2, errors=5,
    ),
    "agent-004": AgentStatus(
        id="agent-004", name="Momentum Hunter", strategy="Momentum",
        status="running", pnl=1876.20, pnl_24h=156.80, trades=89,
        win_rate=48.3, uptime="1d 5h 33m", last_trade="12 min ago",
        memory_mb=768, cpu_pct=22.1, errors=0,
    ),
    "agent-005": AgentStatus(
        id="agent-005", name="DEX Scout", strategy="DEX Arbitrage",
        status="running", pnl=3214.90, pnl_24h=198.40, trades=2156,
        win_rate=68.9, uptime="4d 18h 47m", last_trade="1 min ago",
        memory_mb=640, cpu_pct=15.7, errors=1,
    ),
    "agent-006": AgentStatus(
        id="agent-006", name="LLM Advisor", strategy="LLM Enhanced",
        status="running", pnl=892.40, pnl_24h=45.60, trades=67,
        win_rate=59.7, uptime="5d 0h 12m", last_trade="8 min ago",
        memory_mb=1024, cpu_pct=28.4, errors=0,
    ),
}

STRATEGIES_DB: List[Strategy] = [
    Strategy(name="LP Arbitrage (hzjken)", description="Liquidity pool arbitrage exploiting price differences across DEXs.",
             risk="Medium", expected_return="15-25% APR", best_for="Stable pairs, high-volatility assets", stars=5,
             tags=["arbitrage", "DeFi", "LP"]),
    Strategy(name="Scalping (Mean Reversion)", description="Fast-paced mean reversion exploiting short-term price oscillations.",
             risk="Medium-High", expected_return="8-15% monthly", best_for="High-liquidity pairs, low fees", stars=4,
             tags=["scalping", "mean-reversion", "CEX/DEX"]),
    Strategy(name="Grid Trading", description="Automated grid orders at preset price levels.",
             risk="Low-Medium", expected_return="5-12% monthly", best_for="Ranging markets, BTC/ETH sideway trends", stars=4,
             tags=["grid", "volatility", "automated"]),
    Strategy(name="Momentum", description="Trend-following strategy capturing directional moves.",
             risk="High", expected_return="20-40% (when trending)", best_for="Strong trends, altcoin seasons", stars=3,
             tags=["momentum", "trend", "altcoins"]),
    Strategy(name="DEX Arbitrage (Solana)", description="Cross-Dex arbitrage on Solana ecosystem.",
             risk="Medium", expected_return="12-20% monthly", best_for="Solana ecosystem, SPL tokens", stars=5,
             tags=["solana", "arbitrage", "DEX"]),
    Strategy(name="LLM Enhanced (TradingAgents)", description="AI-powered strategy using multi-agent debate system.",
             risk="Medium (adaptive)", expected_return="Variable (market-aware)", best_for="Dynamic market conditions", stars=5,
             tags=["AI", "LLM", "adaptive", "TradingAgents"]),
    Strategy(name="Hybrid (Multi-Strategy)", description="Combines multiple strategies with dynamic allocation.",
             risk="Medium", expected_return="10-18% monthly", best_for="All market conditions", stars=4,
             tags=["hybrid", "multi-strategy", "regime-aware"]),
    Strategy(name="Autopilot (AI picks)", description="Fully autonomous mode where AI selects strategies in real-time.",
             risk="Medium-High (delegated)", expected_return="Variable", best_for="Hands-off trading", stars=4,
             tags=["autopilot", "AI", "autonomous", "hands-off"]),
]

SELECTED_STRATEGY: str = "LP Arbitrage (hzjken)"


def _generate_pnl_history(days: int = 30) -> List[PnLEntry]:
    """Generate mock P&L history."""
    entries = []
    cumulative = 0
    for i in range(days, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        pnl = random.uniform(-200, 500)
        cumulative += pnl
        entries.append(PnLEntry(date=date, pnl=pnl, pnl_cumulative=cumulative))
    return entries


# -------------------------------------------------------------------
# FastAPI App
# -------------------------------------------------------------------

app = FastAPI(
    title="KEOTrading API",
    description="REST API for KEOTrading dashboard and agent management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to dashboard origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Health Check
# -------------------------------------------------------------------

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# -------------------------------------------------------------------
# Agent Endpoints
# -------------------------------------------------------------------

@app.get("/agents", response_model=List[AgentStatus])
async def list_agents(
    status: Optional[str] = None,
    strategy: Optional[str] = None,
) -> List[AgentStatus]:
    """
    List all agents with optional filtering.

    - **status**: Filter by status (running, paused, stopped, error)
    - **strategy**: Filter by strategy name
    """
    agents = list(AGENTS_DB.values())
    if status:
        agents = [a for a in agents if a.status == status]
    if strategy:
        agents = [a for a in agents if a.strategy == strategy]
    return agents


@app.get("/agents/{agent_id}", response_model=AgentStatus)
async def get_agent(agent_id: str) -> AgentStatus:
    """Get a single agent by ID."""
    if agent_id not in AGENTS_DB:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return AGENTS_DB[agent_id]


@app.post("/agents/{agent_id}/start")
async def start_agent(agent_id: str) -> Dict[str, Any]:
    """Start a stopped agent."""
    if agent_id not in AGENTS_DB:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    AGENTS_DB[agent_id].status = "running"
    return {"success": True, "agent_id": agent_id, "status": "running"}


@app.post("/agents/{agent_id}/stop")
async def stop_agent(agent_id: str) -> Dict[str, Any]:
    """Stop a running agent."""
    if agent_id not in AGENTS_DB:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    AGENTS_DB[agent_id].status = "stopped"
    return {"success": True, "agent_id": agent_id, "status": "stopped"}


@app.post("/agents/{agent_id}/pause")
async def pause_agent(agent_id: str) -> Dict[str, Any]:
    """Pause a running agent."""
    if agent_id not in AGENTS_DB:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    AGENTS_DB[agent_id].status = "paused"
    return {"success": True, "agent_id": agent_id, "status": "paused"}


@app.post("/agents")
async def create_agent(
    name: str,
    strategy: str,
) -> AgentStatus:
    """Create a new agent."""
    agent_id = f"agent-{uuid.uuid4().hex[:8]}"
    agent = AgentStatus(
        id=agent_id,
        name=name,
        strategy=strategy,
        status="running",
    )
    AGENTS_DB[agent_id] = agent
    return agent


# -------------------------------------------------------------------
# Strategy Endpoints
# -------------------------------------------------------------------

@app.get("/strategies", response_model=List[Strategy])
async def list_strategies() -> List[Strategy]:
    """List all available strategies."""
    return STRATEGIES_DB


@app.get("/strategies/current")
async def get_current_strategy() -> Dict[str, str]:
    """Get the currently selected strategy."""
    return {"selected": SELECTED_STRATEGY}


@app.post("/strategies/{strategy_name}/select")
async def select_strategy(strategy_name: str) -> Dict[str, Any]:
    """Select a strategy for active trading."""
    valid_names = [s.name for s in STRATEGIES_DB]
    if strategy_name not in valid_names:
        raise HTTPException(
            status_code=400,
            detail=f"Strategy '{strategy_name}' not found. Available: {valid_names}"
        )
    global SELECTED_STRATEGY
    SELECTED_STRATEGY = strategy_name
    return {"success": True, "selected": strategy_name}


# -------------------------------------------------------------------
# Portfolio Endpoints
# -------------------------------------------------------------------

@app.get("/portfolio", response_model=Portfolio)
async def get_portfolio() -> Portfolio:
    """Get current portfolio state."""
    positions = [
        PortfolioPosition(asset="USDT", amount=45000.0, value_usd=45000.0, allocation=0.45, source="Binance"),
        PortfolioPosition(asset="BTC", amount=0.85, value_usd=25000.0, allocation=0.25, source="CEX"),
        PortfolioPosition(asset="ETH", amount=8.5, value_usd=15000.0, allocation=0.15, source="CEX"),
        PortfolioPosition(asset="SOL", amount=75.0, value_usd=10000.0, allocation=0.10, source="Solana DEX"),
        PortfolioPosition(asset="RAY", amount=500.0, value_usd=1500.0, allocation=0.015, source="Raydium LP"),
        PortfolioPosition(asset="SRM", amount=200.0, value_usd=500.0, allocation=0.005, source="Solana DEX"),
        PortfolioPosition(asset="ORCA", amount=300.0, value_usd=1000.0, allocation=0.01, source="Orca LP"),
        PortfolioPosition(asset="Other", amount=1.0, value_usd=1000.0, allocation=0.01, source="Various"),
    ]
    return Portfolio(
        total_value_usd=sum(p.value_usd for p in positions),
        positions=positions,
        last_updated=datetime.now().isoformat(),
    )


# -------------------------------------------------------------------
# P&L Endpoints
# -------------------------------------------------------------------

@app.get("/pnl", response_model=List[PnLEntry])
async def get_pnl_history(days: int = 30) -> List[PnLEntry]:
    """
    Get P&L history.

    - **days**: Number of days of history to return (default 30, max 365)
    """
    days = min(days, 365)
    return _generate_pnl_history(days)


@app.get("/pnl/summary")
async def get_pnl_summary() -> Dict[str, Any]:
    """Get P&L summary metrics."""
    history = _generate_pnl_history(30)
    total = history[-1].pnl_cumulative
    daily = history[-1].pnl
    return {
        "total_pnl": total,
        "daily_pnl": daily,
        "weekly_pnl": sum(e.pnl for e in history[-7:]),
        "monthly_pnl": total,
        "change_24h_pct": round((daily / abs(history[-2].pnl_cumulative)) * 100, 2) if history else 0,
    }


# -------------------------------------------------------------------
# Run with uvicorn
# -------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
