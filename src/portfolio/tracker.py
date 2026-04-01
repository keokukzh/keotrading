"""
KEOTrading Portfolio Tracker
===========================
Multi-chain portfolio tracking with real-time updates.
Supports: TRON (TRC20), Ethereum (ERC20), BSC (BEP20), Solana (SPL)

Based on crypto-portfolio-tracker skill patterns.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class Network(Enum):
    """Supported blockchain networks."""
    TRON = "tron"
    ETHEREUM = "ethereum"
    BSC = "bsc"
    SOLANA = "solana"


@dataclass
class Position:
    """A trading position."""
    symbol: str
    name: str
    quantity: float
    cost: float  # Average entry price
    current_price: float = 0
    network: str = "ethereum"
    source: str = ""  # Exchange name
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    entry_reason: str = ""
    opened_at: str = ""


@dataclass
class Order:
    """A trading order."""
    id: str
    symbol: str
    side: str  # buy, sell
    order_type: str  # market, limit, stop
    price: float
    quantity: float
    filled: float = 0
    status: str = "pending"  # pending, filled, cancelled
    created_at: str = ""
    filled_at: Optional[str] = None
    fee: float = 0
    network: str = "ethereum"
    exchange: str = ""


@dataclass
class Metrics:
    """Portfolio metrics."""
    current_equity: float = 0
    cash: float = 0
    position_value: float = 0
    unrealized_pnl: float = 0
    realized_pnl: float = 0
    total_return_pct: float = 0
    trade_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    max_drawdown: float = 0
    win_rate: float = 0
    sharpe_ratio: float = 0


class PortfolioTracker:
    """
    Multi-chain portfolio tracker.
    Tracks positions, calculates P&L, manages metrics.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.positions_file = self.data_dir / "positions.json"
        self.orders_file = self.data_dir / "orders.jsonl"
        self.metrics_file = self.data_dir / "metrics.json"
        self.equity_curve_file = self.data_dir / "equity_curve.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self.positions: List[Position] = self._load_positions()
        self.orders: List[Order] = self._load_orders()
        self.metrics = self._load_metrics()
        self.equity_curve: List[Dict] = self._load_equity_curve()
    
    def _load_positions(self) -> List[Position]:
        """Load positions from file."""
        if self.positions_file.exists():
            try:
                with open(self.positions_file) as f:
                    data = json.load(f)
                    return [Position(**p) for p in data]
            except Exception as e:
                logger.error(f"Error loading positions: {e}")
        return []
    
    def _load_orders(self) -> List[Order]:
        """Load orders from file."""
        if self.orders_file.exists():
            try:
                orders = []
                with open(self.orders_file) as f:
                    for line in f:
                        if line.strip():
                            orders.append(Order(**json.loads(line)))
                return orders
            except Exception as e:
                logger.error(f"Error loading orders: {e}")
        return []
    
    def _load_metrics(self) -> Metrics:
        """Load metrics from file."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file) as f:
                    data = json.load(f)
                    return Metrics(**data)
            except Exception as e:
                logger.error(f"Error loading metrics: {e}")
        return Metrics()
    
    def _load_equity_curve(self) -> List[Dict]:
        """Load equity curve from file."""
        if self.equity_curve_file.exists():
            try:
                with open(self.equity_curve_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading equity curve: {e}")
        return []
    
    def _save_positions(self):
        """Save positions to file."""
        try:
            with open(self.positions_file, 'w') as f:
                json.dump([asdict(p) for p in self.positions], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving positions: {e}")
    
    def _append_order(self, order: Order):
        """Append order to file."""
        try:
            with open(self.orders_file, 'a') as f:
                f.write(json.dumps(asdict(order)) + '\n')
        except Exception as e:
            logger.error(f"Error appending order: {e}")
    
    def _save_metrics(self):
        """Save metrics to file."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(asdict(self.metrics), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def _save_equity_curve(self):
        """Save equity curve to file."""
        try:
            with open(self.equity_curve_file, 'w') as f:
                json.dump(self.equity_curve, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving equity curve: {e}")
    
    async def update_prices(self, prices: Dict[str, float]) -> Dict[str, float]:
        """
        Update current prices for all positions.
        Returns updated prices.
        """
        for position in self.positions:
            symbol = position.symbol.replace('/', '')
            # Try multiple symbol formats
            for fmt in [symbol, f"{position.network}:{symbol}", position.symbol]:
                if fmt in prices:
                    position.current_price = prices[fmt]
                    break
        
        self._calculate_metrics()
        return {p.symbol: p.current_price for p in self.positions}
    
    async def fetch_prices_from_coingecko(self) -> Dict[str, float]:
        """Fetch current prices from CoinGecko."""
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,solana,avalanche-2,chainlink,binancecoin",
            "vs_currencies": "usd",
        }
        
        prices = {}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Map CoinGecko IDs to symbols
                mapping = {
                    "bitcoin": "BTC",
                    "ethereum": "ETH",
                    "solana": "SOL",
                    "avalanche-2": "AVAX",
                    "chainlink": "LINK",
                    "binancecoin": "BNB",
                }
                
                for coin_id, symbol in mapping.items():
                    if coin_id in data:
                        prices[symbol] = data[coin_id].get("usd", 0)
                        prices[f"{symbol}/USDT"] = data[coin_id].get("usd", 0)
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
        
        return prices
    
    def _calculate_metrics(self):
        """Calculate portfolio metrics."""
        total_cost = 0
        total_value = 0
        
        for position in self.positions:
            cost = position.quantity * position.cost
            value = position.quantity * position.current_price
            total_cost += cost
            total_value += value
        
        unrealized_pnl = total_value - total_cost
        total_return_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
        
        # Calculate win rate
        closed_positions = [o for o in self.orders if o.status == "filled" and o.side == "sell"]
        if closed_positions:
            wins = sum(1 for o in closed_positions if self._get_position_pnl(o) > 0)
            self.metrics.win_rate = wins / len(closed_positions) * 100
        
        self.metrics.position_value = total_value
        self.metrics.unrealized_pnl = unrealized_pnl
        self.metrics.total_return_pct = total_return_pct
        self.metrics.current_equity = self.metrics.cash + total_value
        
        self._save_metrics()
    
    def _get_position_pnl(self, order: Order) -> float:
        """Calculate P&L for a closed position."""
        # Simplified - would need to match buy/sell orders
        return 0
    
    def add_position(self, position: Position):
        """Add a new position."""
        self.positions.append(position)
        self._save_positions()
        self._calculate_metrics()
    
    def remove_position(self, symbol: str):
        """Remove a position by symbol."""
        self.positions = [p for p in self.positions if p.symbol != symbol]
        self._save_positions()
        self._calculate_metrics()
    
    def add_order(self, order: Order):
        """Add a new order."""
        self.orders.append(order)
        self._append_order(order)
    
    def update_equity_curve(self):
        """Update equity curve with current metrics."""
        entry = {
            "date": datetime.now().isoformat(),
            "equity": self.metrics.current_equity,
            "cash": self.metrics.cash,
            "position_value": self.metrics.position_value,
            "unrealized_pnl": self.metrics.unrealized_pnl,
            "realized_pnl": self.metrics.realized_pnl,
        }
        self.equity_curve.append(entry)
        self._save_equity_curve()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get portfolio summary."""
        return {
            "metrics": asdict(self.metrics),
            "positions_count": len(self.positions),
            "orders_count": len(self.orders),
            "last_updated": datetime.now().isoformat(),
        }


# Global tracker instance
_tracker: Optional[PortfolioTracker] = None


def get_portfolio_tracker() -> PortfolioTracker:
    """Get or create portfolio tracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = PortfolioTracker()
    return _tracker
