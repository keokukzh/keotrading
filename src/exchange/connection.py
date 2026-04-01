"""
Exchange Connection Manager
Handles real exchange connections via CCXT.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import yaml

import ccxt

logger = logging.getLogger(__name__)


@dataclass
class ExchangeConfig:
    """Configuration for an exchange connection."""
    exchange_id: str
    api_key: str
    api_secret: str
    testnet: bool = False
    enabled: bool = True
    max_position_usd: float = 100.0
    fee_tier: float = 0.1  # maker fee %


class ExchangeConnection:
    """Manages live connections to exchanges via CCXT."""
    
    def __init__(self, config: ExchangeConfig):
        self.config = config
        self.exchange = None
        self._connected = False
        self._last_ticker: Dict[str, dict] = {}
        
    def _create_exchange(self) -> ccxt.Exchange:
        """Create CCXT exchange instance."""
        exchange_class = getattr(ccxt, self.config.exchange_id)
        
        exchange_params = {
            'apiKey': self.config.api_key,
            'secret': self.config.api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        }
        
        # Add testnet if enabled
        if self.config.testnet:
            if self.config.exchange_id == 'binance':
                exchange_params['urls'] = {
                    'api': 'https://testnet.binance.vision/api'
                }
            elif self.config.exchange_id == 'bybit':
                exchange_params['urls'] = {
                    'api': 'https://api-testnet.bybit.com'
                }
        
        return exchange_class(exchange_params)
    
    async def connect(self) -> bool:
        """Test connection to exchange."""
        try:
            self.exchange = self._create_exchange()
            
            # Test by fetching account info
            if hasattr(self.exchange, 'fetch_balance'):
                balance = await asyncio.to_thread(self.exchange.fetch_balance)
                self._connected = True
                logger.info(f"✅ Connected to {self.config.exchange_id}")
                return True
            
            self._connected = False
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to {self.config.exchange_id}: {e}")
            self._connected = False
            return False
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def fetch_ticker(self, symbol: str) -> Optional[dict]:
        """Fetch real-time ticker data."""
        if not self._connected:
            return None
        
        try:
            ticker = await asyncio.to_thread(self.exchange.fetch_ticker, symbol)
            self._last_ticker[symbol] = ticker
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker {symbol}: {e}")
            return None
    
    async def fetch_tickers(self, symbols: List[str]) -> Dict[str, dict]:
        """Fetch multiple tickers."""
        results = {}
        for symbol in symbols:
            ticker = await self.fetch_ticker(symbol)
            if ticker:
                results[symbol] = ticker
        return results
    
    async def fetch_balance(self) -> Optional[dict]:
        """Fetch account balances."""
        if not self._connected:
            return None
        
        try:
            return await asyncio.to_thread(self.exchange.fetch_balance)
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None
    
    async def fetch_order_book(self, symbol: str, limit: int = 20) -> Optional[dict]:
        """Fetch order book."""
        if not self._connected:
            return None
        
        try:
            return await asyncio.to_thread(
                self.exchange.fetch_order_book, symbol, limit
            )
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            return None
    
    def place_order(self, symbol: str, type: str, side: str, 
                   amount: float, price: float = None) -> Optional[dict]:
        """Place an order (synchronous)."""
        if not self._connected:
            logger.error("Not connected to exchange")
            return None
        
        try:
            return self.exchange.create_order(symbol, type, side, amount, price)
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    async def place_order_async(self, symbol: str, type: str, side: str,
                                amount: float, price: float = None) -> Optional[dict]:
        """Place an order asynchronously."""
        return await asyncio.to_thread(
            self.place_order, symbol, type, side, amount, price
        )
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order."""
        if not self._connected:
            return False
        
        try:
            await asyncio.to_thread(self.exchange.cancel_order, order_id, symbol)
            return True
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return False
    
    async def fetch_open_orders(self, symbol: str = None) -> List[dict]:
        """Fetch open orders."""
        if not self._connected:
            return []
        
        try:
            return await asyncio.to_thread(
                self.exchange.fetch_open_orders, symbol
            )
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []
    
    async def fetch_my_trades(self, symbol: str = None, limit: int = 50) -> List[dict]:
        """Fetch my recent trades."""
        if not self._connected:
            return []
        
        try:
            return await asyncio.to_thread(
                self.exchange.fetch_my_trades, symbol, limit
            )
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []
    
    def get_trading_fee(self, symbol: str = None) -> float:
        """Get trading fee rate."""
        if hasattr(self.exchange, 'fees') and 'trading' in self.exchange.fees:
            return self.exchange.fees['trading'].get('maker', 0.001)
        return 0.001  # Default 0.1%
    
    def get_last_price(self, symbol: str) -> Optional[float]:
        """Get last known price from cache."""
        if symbol in self._last_ticker:
            return self._last_ticker[symbol].get('last')
        return None
    
    def get_spread(self, symbol: str) -> Optional[float]:
        """Get bid-ask spread."""
        if symbol in self._last_ticker:
            ticker = self._last_ticker[symbol]
            bid = ticker.get('bid', 0)
            ask = ticker.get('ask', 0)
            if bid and ask:
                return (ask - bid) / ask * 100
        return None


class ExchangeManager:
    """Manages multiple exchange connections."""
    
    def __init__(self, config_path: str = "configs/exchanges.yaml"):
        self.config_path = config_path
        self.connections: Dict[str, ExchangeConnection] = {}
        self._load_config()
    
    def _load_config(self):
        """Load exchange configurations from YAML."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            for exchange_id, settings in config.get('exchanges', {}).items():
                if settings.get('enabled', False):
                    config_obj = ExchangeConfig(
                        exchange_id=exchange_id,
                        api_key=settings.get('api_key', ''),
                        api_secret=settings.get('api_secret', ''),
                        testnet=settings.get('testnet', False),
                        enabled=True,
                        max_position_usd=settings.get('max_position_usd', 100.0),
                        fee_tier=settings.get('fee_tier', 0.1)
                    )
                    self.connections[exchange_id] = ExchangeConnection(config_obj)
                    logger.info(f"Loaded config for {exchange_id}")
                    
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all enabled exchanges."""
        results = {}
        for exchange_id, conn in self.connections.items():
            results[exchange_id] = await conn.connect()
        return results
    
    async def connect_exchange(self, exchange_id: str) -> bool:
        """Connect to a specific exchange."""
        if exchange_id in self.connections:
            return await self.connections[exchange_id].connect()
        return False
    
    def get_connection(self, exchange_id: str) -> Optional[ExchangeConnection]:
        """Get connection for an exchange."""
        return self.connections.get(exchange_id)
    
    def get_connected_exchanges(self) -> List[str]:
        """Get list of successfully connected exchanges."""
        return [
            exchange_id for exchange_id, conn in self.connections.items()
            if conn.is_connected
        ]
    
    async def get_total_balance_usd(self, quote: str = 'USDT') -> float:
        """Get total portfolio value in USD."""
        total = 0.0
        
        for conn in self.connections.values():
            if not conn.is_connected:
                continue
            
            balance = await conn.fetch_balance()
            if not balance:
                continue
            
            for currency, info in balance.get('total', {}).items():
                if info <= 0:
                    continue
                
                # Get price
                if currency == quote:
                    total += info
                else:
                    symbol = f"{currency}/{quote}"
                    price = conn.get_last_price(symbol)
                    if price:
                        total += info * price
        
        return total
    
    async def get_portfolio_distribution(self) -> Dict[str, float]:
        """Get portfolio as percentage allocation."""
        distribution = {}
        total_value = await self.get_total_balance_usd()
        
        if total_value == 0:
            return distribution
        
        for conn in self.connections.values():
            if not conn.is_connected:
                continue
            
            balance = await conn.fetch_balance()
            if not balance:
                continue
            
            for currency, info in balance.get('total', {}).items():
                if info <= 0:
                    continue
                
                symbol = f"{currency}/USDT"
                price = conn.get_last_price(symbol) or 1.0
                value = info * price
                
                if currency in distribution:
                    distribution[currency] += value
                else:
                    distribution[currency] = value
        
        # Convert to percentages
        return {
            k: round(v / total_value * 100, 2) 
            for k, v in distribution.items()
        }
