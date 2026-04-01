"""
Simulation Engine
================
Executes simulated orders against real market prices.
Handles slippage, fees, and order matching.
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

import httpx

logger = logging.getLogger(__name__)


# Slippage model based on order size and liquidity
SLIPPAGE_MODEL = {
    "large_market": 0.001,   # 0.1% for large liquid pairs
    "small_market": 0.005,     # 0.5% for illiquid
    "stablecoin": 0.0001,     # 0.01% for USDT/USDC
    "default": 0.002,          # 0.2% default
}

# Fee model (simulated exchange fees)
FEE_MODEL = {
    "maker": 0.001,   # 0.1% maker fee
    "taker": 0.005,   # 0.5% taker fee
}


@dataclass
class MarketPrice:
    """Current market price data."""
    symbol: str
    last: float
    bid: float
    ask: float
    spread: float = 0
    source: str = "coingecko"
    timestamp: str = ""


class SimulationEngine:
    """
    Simulation engine for demo trading.
    - Fetches real prices
    - Calculates slippage
    - Executes orders with realistic fees
    """
    
    def __init__(self, portfolio=None):
        self.portfolio = portfolio
        self.prices: Dict[str, MarketPrice] = {}
        self._running = False
        self._price_task = None
    
    def set_portfolio(self, portfolio):
        """Set the portfolio to manage."""
        self.portfolio = portfolio
    
    async def fetch_prices(self) -> Dict[str, MarketPrice]:
        """Fetch current prices from CoinGecko."""
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,solana,avalanche-2,chainlink,binancecoin",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }
        
        symbol_map = {
            "bitcoin": "BTC/USDT",
            "ethereum": "ETH/USDT",
            "solana": "SOL/USDT",
            "avalanche-2": "AVAX/USDT",
            "chainlink": "LINK/USDT",
            "binancecoin": "BNB/USDT",
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for coin_id, symbol in symbol_map.items():
                    if coin_id in data:
                        price_data = data[coin_id]
                        last = price_data.get("usd", 0)
                        
                        # Calculate realistic bid/ask spread
                        spread_pct = 0.0005  # 0.05% spread
                        spread = last * spread_pct
                        
                        self.prices[symbol] = MarketPrice(
                            symbol=symbol,
                            last=last,
                            bid=last - spread/2,
                            ask=last + spread/2,
                            spread=spread,
                            source="coingecko",
                            timestamp=datetime.now().isoformat(),
                        )
                
                return self.prices
                
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return self.prices
    
    def calculate_slippage(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
    ) -> float:
        """
        Calculate expected slippage for an order.
        Returns slippage as a decimal (e.g., 0.002 = 0.2%)
        """
        # Base slippage on order size
        price = self.prices.get(symbol)
        if not price:
            return SLIPPAGE_MODEL["default"]
        
        # Order value in USD
        order_value = price.last * quantity
        
        # Larger orders = more slippage
        if order_value > 100000:  # > $100k
            base_slippage = SLIPPAGE_MODEL["large_market"]
        elif order_value > 10000:  # > $10k
            base_slippage = 0.003
        else:
            base_slippage = 0.001
        
        # Stablecoins have less slippage
        if "USDT" in symbol or "USDC" in symbol:
            base_slippage = SLIPPAGE_MODEL["stablecoin"]
        
        # Market orders have slippage, limit orders don't
        if order_type == "limit":
            return 0
        
        # Add randomness (±20%)
        random_factor = 0.8 + random.random() * 0.4
        return base_slippage * random_factor
    
    def calculate_fee(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float,
    ) -> float:
        """
        Calculate trading fee.
        Returns fee in quote currency (e.g., USDT).
        """
        fee_rate = FEE_MODEL["taker"] if order_type == "market" else FEE_MODEL["maker"]
        order_value = price * quantity
        return order_value * fee_rate
    
    async def execute_order(
        self,
        order,
        current_price: float = None,
    ) -> Dict[str, Any]:
        """
        Execute an order against current market price.
        Returns execution details.
        """
        if not self.portfolio:
            return {"success": False, "error": "No portfolio set"}
        
        # Get current price
        price_data = self.prices.get(order.symbol)
        if not price_data:
            if not current_price:
                return {"success": False, "error": f"No price for {order.symbol}"}
            price_data = MarketPrice(
                symbol=order.symbol,
                last=current_price,
                bid=current_price,
                ask=current_price,
            )
        
        # Determine execution price
        if order.order_type == "market":
            # Market order: execute at current price ± slippage
            slippage = self.calculate_slippage(
                order.symbol, order.side, order.quantity, order.order_type
            )
            
            if order.side == "buy":
                # Buy at ask (higher)
                exec_price = price_data.ask * (1 + slippage)
            else:
                # Sell at bid (lower)
                exec_price = price_data.bid * (1 - slippage)
        else:
            # Limit order: execute at specified price
            exec_price = order.price
        
        # Calculate fee
        fee = self.calculate_fee(
            order.symbol, order.side, order.order_type, order.quantity, exec_price
        )
        
        # Calculate actual slippage
        actual_slippage = abs(exec_price - price_data.last) / price_data.last
        
        # Execute the order
        success = self.portfolio.fill_order(
            order_id=order.id,
            filled_price=exec_price,
            slippage=actual_slippage,
            fee=fee,
        )
        
        return {
            "success": success,
            "order_id": order.id,
            "symbol": order.symbol,
            "side": order.side,
            "exec_price": exec_price,
            "market_price": price_data.last,
            "slippage": actual_slippage,
            "fee": fee,
            "quantity": order.quantity,
            "total_value": exec_price * order.quantity,
        }
    
    async def start_price_updates(self, interval: int = 30):
        """
        Start background price updates.
        Updates prices every `interval` seconds.
        """
        self._running = True
        
        while self._running:
            try:
                await self.fetch_prices()
                
                # Update portfolio prices
                if self.portfolio:
                    prices_dict = {sym: p.last for sym, p in self.prices.items()}
                    self.portfolio.update_prices(prices_dict)
                    self.portfolio.record_equity()
                
                logger.info(f"Updated {len(self.prices)} prices")
                
            except Exception as e:
                logger.error(f"Error in price update loop: {e}")
            
            await asyncio.sleep(interval)
    
    def stop_price_updates(self):
        """Stop background price updates."""
        self._running = False
    
    async def run_order_simulation(self, order) -> Dict[str, Any]:
        """
        Run a complete order simulation.
        Creates order, executes it, returns results.
        """
        if not self.portfolio:
            return {"success": False, "error": "No portfolio"}
        
        # Create order in portfolio
        created_order = self.portfolio.create_order(
            symbol=order["symbol"],
            side=order["side"],
            order_type=order.get("order_type", "market"),
            quantity=order["quantity"],
            price=order.get("price", 0),
        )
        
        # Execute it
        result = await self.execute_order(created_order)
        result["order_id"] = created_order.id
        
        return result


# Global engine instance
_engine: Optional[SimulationEngine] = None


def get_simulation_engine() -> SimulationEngine:
    """Get or create simulation engine singleton."""
    global _engine
    if _engine is None:
        _engine = SimulationEngine()
    return _engine
