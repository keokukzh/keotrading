"""
Real-time Data Manager
Replaces mock data with live exchange data.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd

from src.exchange.connection import ExchangeManager, ExchangeConnection

logger = logging.getLogger(__name__)


@dataclass
class AgentPnL:
    """P&L data for an agent."""
    agent_id: str
    agent_name: str
    strategy: str
    status: str
    pnl: float
    pnl_24h: float
    trades: int
    win_rate: float
    uptime: str
    last_trade: str


@dataclass
class PortfolioSnapshot:
    """Portfolio state at a point in time."""
    timestamp: datetime
    total_value_usd: float
    positions: Dict[str, float]  # asset -> amount
    pnl_daily: float
    pnl_weekly: float
    pnl_monthly: float


class RealTimeDataManager:
    """Fetches and manages real-time market data from exchanges."""
    
    def __init__(self, exchange_manager: ExchangeManager):
        self.exchange_manager = exchange_manager
        self._portfolio_history: List[PortfolioSnapshot] = []
        self._trade_history: List[dict] = []
        self._agent_states: Dict[str, dict] = {}
        self._last_update: Optional[datetime] = None
        self._update_interval = 30  # seconds
    
    async def refresh_all(self):
        """Refresh all data from exchanges."""
        await self._update_balances()
        await self._update_tickers()
        self._last_update = datetime.now()
    
    async def _update_balances(self):
        """Update account balances from all connected exchanges."""
        for exchange_id, conn in self.exchange_manager.connections.items():
            if not conn.is_connected:
                continue
            
            try:
                balance = await conn.fetch_balance()
                if balance:
                    self._agent_states[exchange_id] = {
                        'balance': balance,
                        'last_update': datetime.now()
                    }
            except Exception as e:
                logger.error(f"Error updating balance for {exchange_id}: {e}")
    
    async def _update_tickers(self):
        """Update ticker data for tracked symbols."""
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT']
        
        for exchange_id, conn in self.exchange_manager.connections.items():
            if not conn.is_connected:
                continue
            
            for symbol in symbols:
                try:
                    ticker = await conn.fetch_ticker(symbol)
                    if ticker:
                        self._agent_states[f"{exchange_id}_{symbol}"] = {
                            'ticker': ticker,
                            'last_update': datetime.now()
                        }
                except Exception as e:
                    logger.error(f"Error updating ticker {symbol} for {exchange_id}: {e}")
    
    async def get_portfolio_value(self) -> float:
        """Get total portfolio value in USD."""
        return await self.exchange_manager.get_total_balance_usd()
    
    async def get_balance(self, exchange_id: str) -> Optional[dict]:
        """Get balance for specific exchange."""
        conn = self.exchange_manager.get_connection(exchange_id)
        if conn and conn.is_connected:
            return await conn.fetch_balance()
        return None
    
    async def get_ticker(self, exchange_id: str, symbol: str) -> Optional[dict]:
        """Get ticker for specific exchange and symbol."""
        conn = self.exchange_manager.get_connection(exchange_id)
        if conn and conn.is_connected:
            return await conn.fetch_ticker(symbol)
        return None
    
    async def get_spread(self, exchange_id: str, symbol: str) -> Optional[float]:
        """Get bid-ask spread for symbol."""
        conn = self.exchange_manager.get_connection(exchange_id)
        if conn:
            return conn.get_spread(symbol)
        return None
    
    def get_last_update_time(self) -> Optional[datetime]:
        """Get timestamp of last data update."""
        return self._last_update
    
    def is_stale(self, max_age_seconds: int = 60) -> bool:
        """Check if data is stale."""
        if not self._last_update:
            return True
        return (datetime.now() - self._last_update).total_seconds() > max_age_seconds


class MockDataGenerator:
    """Generates realistic mock data when no exchange connection is available."""
    
    @staticmethod
    def generate_pnl_history(days: int = 30) -> pd.DataFrame:
        """Generate mock P&L history."""
        import random
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days, -1, -1)]
        cumulative = 10000
        values = []
        
        for i in range(days + 1):
            daily_change = random.uniform(-500, 800)
            cumulative += daily_change
            values.append(round(cumulative, 2))
        
        return pd.DataFrame({"date": dates, "pnl": values})
    
    @staticmethod
    def generate_agent_status() -> List[AgentPnL]:
        """Generate mock agent P&L data."""
        import random
        
        agents = [
            AgentPnL(
                agent_id="agent-001",
                agent_name="Hzjken LP Agent",
                strategy="LP Arbitrage",
                status="running",
                pnl=random.uniform(1000, 8000),
                pnl_24h=random.uniform(-200, 500),
                trades=random.randint(500, 3000),
                win_rate=random.uniform(55, 80),
                uptime="6d 14h",
                last_trade="2 min ago"
            ),
            AgentPnL(
                agent_id="agent-002",
                agent_name="Scalper Alpha",
                strategy="Scalping",
                status="running",
                pnl=random.uniform(500, 4000),
                pnl_24h=random.uniform(-100, 300),
                trades=random.randint(1000, 5000),
                win_rate=random.uniform(50, 70),
                uptime="3d 2h",
                last_trade="30 sec ago"
            ),
            AgentPnL(
                agent_id="agent-003",
                agent_name="Grid Bot Beta",
                strategy="Grid Trading",
                status="paused",
                pnl=random.uniform(-500, 500),
                pnl_24h=random.uniform(-100, 100),
                trades=random.randint(100, 500),
                win_rate=random.uniform(45, 65),
                uptime="2d 8h",
                last_trade="4h ago"
            ),
            AgentPnL(
                agent_id="agent-004",
                agent_name="Momentum Hunter",
                strategy="Momentum",
                status="running",
                pnl=random.uniform(500, 5000),
                pnl_24h=random.uniform(-200, 600),
                trades=random.randint(50, 500),
                win_rate=random.uniform(40, 60),
                uptime="1d 5h",
                last_trade="12 min ago"
            ),
            AgentPnL(
                agent_id="agent-005",
                agent_name="DEX Scout",
                strategy="DEX Arbitrage",
                status="running",
                pnl=random.uniform(1000, 6000),
                pnl_24h=random.uniform(-100, 400),
                trades=random.randint(500, 4000),
                win_rate=random.uniform(60, 80),
                uptime="4d 18h",
                last_trade="1 min ago"
            ),
            AgentPnL(
                agent_id="agent-006",
                agent_name="LLM Advisor",
                strategy="LLM Enhanced",
                status="running",
                pnl=random.uniform(200, 2000),
                pnl_24h=random.uniform(-50, 200),
                trades=random.randint(20, 200),
                win_rate=random.uniform(50, 70),
                uptime="5d 0h",
                last_trade="8 min ago"
            ),
        ]
        return agents
    
    @staticmethod
    def generate_portfolio_allocation() -> Dict[str, float]:
        """Generate mock portfolio allocation."""
        import random
        # Generate realistic-looking allocation
        btc = random.uniform(20, 35)
        eth = random.uniform(15, 25)
        sol = random.uniform(8, 15)
        usdt = random.uniform(20, 35)
        other = 100 - btc - eth - sol - usdt
        
        return {
            "BTC": round(btc, 2),
            "ETH": round(eth, 2),
            "SOL": round(sol, 2),
            "USDT": round(usdt, 2),
            "Other": round(max(other, 5), 2)
        }
    
    @staticmethod
    def generate_total_pnl() -> dict:
        """Generate mock total P&L summary."""
        import random
        total = random.uniform(10000, 25000)
        return {
            "total": round(total, 2),
            "daily": round(random.uniform(-500, 1000), 2),
            "weekly": round(random.uniform(1000, 5000), 2),
            "monthly": round(total, 2),
            "change_24h": round(random.uniform(-5, 8), 2),
        }
