"""
Demo Trading Agents
=================
Simulated trading agents that generate signals and execute demo trades.
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Available trading strategies."""
    MEAN_REVERSION = "mean_reversion"
    GRID_TRADING = "grid_trading"
    MOMENTUM = "momentum"
    RANDOM = "random"


@dataclass
class TradingSignal:
    """A trading signal from an agent."""
    id: str
    agent_id: str
    strategy: str
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    entry_price: float
    stop_loss: float = 0
    take_profit: float = 0
    confidence: float = 0  # 0-1
    reason: str = ""
    timestamp: str = ""
    executed: bool = False


@dataclass
class DemoAgent:
    """A demo trading agent."""
    id: str
    name: str
    strategy: StrategyType
    enabled: bool = False
    running: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)
    signals: List[TradingSignal] = field(default_factory=list)


class DemoTradingAgents:
    """
    Demo trading agents that generate signals.
    These agents simulate trading decisions but use the virtual portfolio.
    """
    
    def __init__(self, simulation_engine=None, virtual_portfolio=None):
        self.engine = simulation_engine
        self.portfolio = virtual_portfolio
        
        # Initialize demo agents
        self.agents: Dict[str, DemoAgent] = {
            "mean_reversion": DemoAgent(
                id="mean_reversion",
                name="Mean Reversion Bot",
                strategy=StrategyType.MEAN_REVERSION,
                parameters={
                    "period": 20,  # MA period
                    "buy_threshold": -0.02,  # -2% from MA
                    "sell_threshold": 0.02,  # +2% from MA
                    "position_size": 0.1,  # 10% of portfolio
                }
            ),
            "grid_trading": DemoAgent(
                id="grid_trading",
                name="Grid Trading Bot",
                strategy=StrategyType.GRID_TRADING,
                parameters={
                    "grid_size": 5,  # Number of grid levels
                    "price_range": 0.1,  # ±10% from current price
                    "order_size": 0.02,  # 2% per grid level
                }
            ),
            "momentum": DemoAgent(
                id="momentum",
                name="Momentum Bot",
                strategy=StrategyType.MOMENTUM,
                parameters={
                    "lookback": 10,  # candles to check
                    "breakout_threshold": 0.005,  # 0.5% breakout
                    "position_size": 0.15,  # 15% of portfolio
                }
            ),
        }
        
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    def set_engine(self, engine):
        """Set the simulation engine."""
        self.engine = engine
    
    def set_portfolio(self, portfolio):
        """Set the virtual portfolio."""
        self.portfolio = portfolio
    
    async def generate_mean_reversion_signal(
        self,
        symbol: str,
        current_price: float,
        prices_history: List[float] = None,
    ) -> Optional[TradingSignal]:
        """Generate a mean reversion signal."""
        if prices_history is None:
            # Generate demo history
            prices_history = [current_price * (1 + random.uniform(-0.05, 0.05)) 
                           for _ in range(20)]
        
        # Calculate simple moving average
        sma = sum(prices_history) / len(prices_history)
        deviation = (current_price - sma) / sma
        
        params = self.agents["mean_reversion"].parameters
        
        # Generate signal based on deviation
        if deviation < params["buy_threshold"]:
            # Price is below MA - potential buy
            return TradingSignal(
                id=f"sig_{random.randint(100000, 999999)}",
                agent_id="mean_reversion",
                strategy="Mean Reversion",
                symbol=symbol,
                side="buy",
                quantity=self._calculate_position_size(symbol, current_price, params["position_size"]),
                entry_price=current_price,
                stop_loss=current_price * 0.98,  # -2% stop
                take_profit=current_price * 1.05,  # +5% target
                confidence=min(abs(deviation) / abs(params["buy_threshold"]), 1.0),
                reason=f"Price {deviation*100:.2f}% below MA ({sma:.2f})",
                timestamp=datetime.now().isoformat(),
            )
        
        elif deviation > params["sell_threshold"]:
            # Price is above MA - potential sell
            return TradingSignal(
                id=f"sig_{random.randint(100000, 999999)}",
                agent_id="mean_reversion",
                strategy="Mean Reversion",
                symbol=symbol,
                side="sell",
                quantity=self._calculate_position_size(symbol, current_price, params["position_size"]),
                entry_price=current_price,
                stop_loss=current_price * 1.02,  # +2% stop
                take_profit=current_price * 0.95,  # -5% target
                confidence=min(abs(deviation) / abs(params["sell_threshold"]), 1.0),
                reason=f"Price {deviation*100:.2f}% above MA ({sma:.2f})",
                timestamp=datetime.now().isoformat(),
            )
        
        return None
    
    async def generate_grid_signals(
        self,
        symbol: str,
        current_price: float,
    ) -> List[TradingSignal]:
        """Generate grid trading signals."""
        params = self.agents["grid_trading"].parameters
        signals = []
        
        grid_size = params["grid_size"]
        price_range = params["price_range"]
        
        # Calculate grid levels
        lower = current_price * (1 - price_range)
        upper = current_price * (1 + price_range)
        step = (upper - lower) / (grid_size + 1)
        
        for i in range(1, grid_size + 1):
            level_price = lower + i * step
            side = "buy" if i <= grid_size // 2 else "sell"
            
            signal = TradingSignal(
                id=f"sig_{random.randint(100000, 999999)}",
                agent_id="grid_trading",
                strategy="Grid Trading",
                symbol=symbol,
                side=side,
                quantity=self._calculate_position_size(symbol, level_price, params["order_size"]),
                entry_price=level_price,
                confidence=0.7,
                reason=f"Grid level {i}/{grid_size} at {level_price:.2f}",
                timestamp=datetime.now().isoformat(),
            )
            signals.append(signal)
        
        return signals
    
    async def generate_momentum_signal(
        self,
        symbol: str,
        current_price: float,
        prices_history: List[float] = None,
    ) -> Optional[TradingSignal]:
        """Generate a momentum/trend following signal."""
        if prices_history is None:
            prices_history = [current_price * (1 + random.uniform(-0.02, 0.02))
                           for _ in range(10)]
        
        params = self.agents["momentum"].parameters
        lookback = min(params["lookback"], len(prices_history))
        
        # Check for breakout
        recent_prices = prices_history[-lookback:]
        high = max(recent_prices)
        low = min(recent_prices)
        
        threshold = params["breakout_threshold"]
        
        # Bullish breakout
        if current_price >= high * (1 + threshold):
            return TradingSignal(
                id=f"sig_{random.randint(100000, 999999)}",
                agent_id="momentum",
                strategy="Momentum",
                symbol=symbol,
                side="buy",
                quantity=self._calculate_position_size(symbol, current_price, params["position_size"]),
                entry_price=current_price,
                stop_loss=low,  # Stop at recent low
                take_profit=current_price * 1.10,  # +10% target
                confidence=0.8,
                reason=f"Bullish breakout above {high:.2f}",
                timestamp=datetime.now().isoformat(),
            )
        
        # Bearish breakdown
        elif current_price <= low * (1 - threshold):
            return TradingSignal(
                id=f"sig_{random.randint(100000, 999999)}",
                agent_id="momentum",
                strategy="Momentum",
                symbol=symbol,
                side="sell",
                quantity=self._calculate_position_size(symbol, current_price, params["position_size"]),
                entry_price=current_price,
                stop_loss=high,  # Stop at recent high
                take_profit=current_price * 0.90,  # -10% target
                confidence=0.8,
                reason=f"Bearish breakdown below {low:.2f}",
                timestamp=datetime.now().isoformat(),
            )
        
        return None
    
    def _calculate_position_size(
        self,
        symbol: str,
        price: float,
        portfolio_pct: float = 0.1,
    ) -> float:
        """Calculate position size in base currency."""
        if not self.portfolio:
            return 0.1  # Default 0.1 BTC
        
        equity = self.portfolio.metrics.current_equity
        position_value = equity * portfolio_pct
        
        # Convert to quantity
        quantity = position_value / price
        return round(quantity, 6)
    
    async def start_agent(self, agent_id: str):
        """Start a demo agent."""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        agent.enabled = True
        agent.running = True
        
        # Start background task
        task = asyncio.create_task(self._run_agent_loop(agent_id))
        self._running_tasks[agent_id] = task
        
        logger.info(f"Started demo agent: {agent_id}")
        return True
    
    async def stop_agent(self, agent_id: str):
        """Stop a demo agent."""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        agent.running = False
        
        # Cancel task
        if agent_id in self._running_tasks:
            self._running_tasks[agent_id].cancel()
            del self._running_tasks[agent_id]
        
        logger.info(f"Stopped demo agent: {agent_id}")
        return True
    
    async def _run_agent_loop(self, agent_id: str):
        """Run agent trading loop."""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        
        while agent.running:
            try:
                # Fetch prices
                if self.engine:
                    await self.engine.fetch_prices()
                
                # Generate signals based on strategy
                for symbol in symbols:
                    price_data = self.engine.prices.get(symbol) if self.engine else None
                    if not price_data:
                        continue
                    
                    current_price = price_data.last
                    
                    if agent.strategy == StrategyType.MEAN_REVERSION:
                        signal = await self.generate_mean_reversion_signal(
                            symbol, current_price
                        )
                        if signal:
                            await self._execute_signal(signal)
                    
                    elif agent.strategy == StrategyType.GRID_TRADING:
                        signals = await self.generate_grid_signals(
                            symbol, current_price
                        )
                        for sig in signals:
                            await self._execute_signal(sig)
                    
                    elif agent.strategy == StrategyType.MOMENTUM:
                        signal = await self.generate_momentum_signal(
                            symbol, current_price
                        )
                        if signal:
                            await self._execute_signal(signal)
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Agent {agent_id} error: {e}")
                await asyncio.sleep(10)
    
    async def _execute_signal(self, signal: TradingSignal):
        """Execute a trading signal."""
        if signal.executed or not self.engine or not self.portfolio:
            return
        
        try:
            # Create and execute order
            order = {
                "symbol": signal.symbol,
                "side": signal.side,
                "order_type": "market",
                "quantity": signal.quantity,
            }
            
            result = await self.engine.run_order_simulation(order)
            
            if result.get("success"):
                signal.executed = True
                self.agents[signal.agent_id].signals.append(signal)
                logger.info(f"Executed {signal.side} signal for {signal.symbol}: {result}")
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
    
    def get_agent_status(self) -> List[Dict]:
        """Get status of all agents."""
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "strategy": agent.strategy.value,
                "enabled": agent.enabled,
                "running": agent.running,
                "signals_generated": len(agent.signals),
                "signals_executed": sum(1 for s in agent.signals if s.executed),
                "parameters": agent.parameters,
            }
            for agent in self.agents.values()
        ]


# Global agents instance
_agents: Optional[DemoTradingAgents] = None


def get_demo_agents() -> DemoTradingAgents:
    """Get or create demo trading agents singleton."""
    global _agents
    if _agents is None:
        _agents = DemoTradingAgents()
    return _agents
