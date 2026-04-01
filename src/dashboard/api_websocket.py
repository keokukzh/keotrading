"""
KEOTrading WebSocket Server
===========================
Real-time data streaming for the new frontend.
Supports: portfolio updates, P&L, agent status, price tickers.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
import threading

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages all active WebSocket connections."""
    
    def __init__(self):
        # Channel -> set of websockets
        self.channels: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, channel: str = "global"):
        """Accept a new WebSocket connection and subscribe to a channel."""
        await websocket.accept()
        
        async with self._lock:
            if channel not in self.channels:
                self.channels[channel] = set()
            self.channels[channel].add(websocket)
        
        logger.info(f"WebSocket connected: {channel}")
    
    async def disconnect(self, websocket: WebSocket, channel: str = "global"):
        """Remove a WebSocket from its channel."""
        async with self._lock:
            if channel in self.channels:
                self.channels[channel].discard(websocket)
                if not self.channels[channel]:
                    del self.channels[channel]
        
        logger.info(f"WebSocket disconnected: {channel}")
    
    async def broadcast(self, channel: str, message: dict):
        """Broadcast a message to all clients in a channel."""
        async with self._lock:
            clients = self.channels.get(channel, set()).copy()
        
        dead_clients = set()
        for client in clients:
            try:
                await client.send_json(message)
            except Exception:
                dead_clients.add(client)
        
        # Cleanup dead clients
        if dead_clients:
            async with self._lock:
                for client in dead_clients:
                    for ch in self.channels:
                        self.channels[ch].discard(client)


class DataStreamer:
    """Streams real-time data to WebSocket clients."""
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}
        self._exchange_manager = None
        self._last_portfolio_snapshot: Dict[str, Any] = {}
    
    def set_exchange_manager(self, exchange_manager):
        """Set the exchange manager for data fetching."""
        self._exchange_manager = exchange_manager
    
    async def start(self):
        """Start all data streaming tasks."""
        self._running = True
        
        # Start streaming tasks
        self._tasks['portfolio'] = asyncio.create_task(self._stream_portfolio())
        self._tasks['prices'] = asyncio.create_task(self._stream_prices())
        self._tasks['agents'] = asyncio.create_task(self._stream_agents())
        
        logger.info("Data streamer started")
    
    async def stop(self):
        """Stop all streaming tasks."""
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        logger.info("Data streamer stopped")
    
    async def _stream_portfolio(self):
        """Stream portfolio updates every 5 seconds."""
        while self._running:
            try:
                if self._exchange_manager:
                    portfolio = await self._fetch_portfolio()
                    if portfolio != self._last_portfolio_snapshot:
                        self._last_portfolio_snapshot = portfolio
                        await self.manager.broadcast("portfolio", {
                            "type": "portfolio_update",
                            "data": portfolio,
                            "timestamp": datetime.now().isoformat()
                        })
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Portfolio stream error: {e}")
                await asyncio.sleep(5)
    
    async def _stream_prices(self):
        """Stream price updates every 2 seconds."""
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT', 'LINK/USDT']
        
        while self._running:
            try:
                if self._exchange_manager:
                    prices = await self._fetch_prices(symbols)
                    await self.manager.broadcast("prices", {
                        "type": "price_update",
                        "data": prices,
                        "timestamp": datetime.now().isoformat()
                    })
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Price stream error: {e}")
                await asyncio.sleep(2)
    
    async def _stream_agents(self):
        """Stream agent status updates every 10 seconds."""
        while self._running:
            try:
                agents = await self._fetch_agents()
                await self.manager.broadcast("agents", {
                    "type": "agent_update",
                    "data": agents,
                    "timestamp": datetime.now().isoformat()
                })
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Agent stream error: {e}")
                await asyncio.sleep(10)
    
    async def _fetch_portfolio(self) -> Dict[str, Any]:
        """Fetch current portfolio from exchanges."""
        positions = []
        total_value = 0.0
        
        if not self._exchange_manager:
            return {"positions": [], "total_value": 0}
        
        connected = self._exchange_manager.get_connected_exchanges()
        
        for exchange_id in connected:
            conn = self._exchange_manager.get_connection(exchange_id)
            if not conn or not conn.is_connected:
                continue
            
            try:
                balance = await conn.fetch_balance()
                if not balance:
                    continue
                
                for currency, info in balance.get('total', {}).items():
                    if info <= 0:
                        continue
                    
                    if currency in ['USDT', 'USDC', 'USD']:
                        value_usd = float(info)
                    else:
                        symbol = f"{currency}/USDT"
                        price = conn.get_last_price(symbol)
                        if price:
                            value_usd = float(info) * price
                        else:
                            value_usd = 0
                    
                    if value_usd > 0.01:
                        total_value += value_usd
                        positions.append({
                            'asset': currency,
                            'amount': float(info),
                            'value_usd': round(value_usd, 2),
                            'source': exchange_id
                        })
            except Exception as e:
                logger.error(f"Error fetching portfolio from {exchange_id}: {e}")
        
        # Calculate allocations
        if total_value > 0:
            for pos in positions:
                pos['allocation'] = round(pos['value_usd'] / total_value * 100, 2)
        
        return {
            "positions": positions,
            "total_value": round(total_value, 2),
            "last_updated": datetime.now().isoformat()
        }
    
    async def _fetch_prices(self, symbols: list) -> Dict[str, dict]:
        """Fetch current prices for symbols."""
        prices = {}
        
        if not self._exchange_manager:
            return prices
        
        connected = self._exchange_manager.get_connected_exchanges()
        
        for exchange_id in connected:
            conn = self._exchange_manager.get_connection(exchange_id)
            if not conn or not conn.is_connected:
                continue
            
            for symbol in symbols:
                try:
                    ticker = await conn.fetch_ticker(symbol)
                    if ticker:
                        prices[symbol] = {
                            'last': ticker.get('last'),
                            'bid': ticker.get('bid'),
                            'ask': ticker.get('ask'),
                            'volume': ticker.get('quoteVolume'),
                            'change_24h': ticker.get('percentage'),
                            'high': ticker.get('high'),
                            'low': ticker.get('low'),
                            'source': exchange_id
                        }
                except Exception:
                    pass
        
        return prices
    
    async def _fetch_agents(self) -> list:
        """Fetch agent status."""
        if not self._exchange_manager:
            return []
        
        connected = self._exchange_manager.get_connected_exchanges()
        agents = []
        
        for exchange_id in connected:
            conn = self._exchange_manager.get_connection(exchange_id)
            agents.append({
                "id": exchange_id,
                "name": f"{exchange_id.title()} Agent",
                "strategy": "Multi-Strategy",
                "status": "running" if conn and conn.is_connected else "stopped",
                "pnl": 0,
                "uptime": "Connected" if conn and conn.is_connected else "Disconnected"
            })
        
        return agents


# =============================================================================
# FastAPI WebSocket Application
# =============================================================================

app_ws = FastAPI(title="KEOTrading WebSocket Server")

app_ws.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
manager = ConnectionManager()
streamer = DataStreamer(manager)


@app_ws.on_event("startup")
async def startup():
    """Initialize on startup."""
    # Import and set exchange manager
    try:
        from src.exchange.connection import ExchangeManager
        streamer.set_exchange_manager(ExchangeManager())
    except Exception as e:
        logger.warning(f"Could not initialize exchange manager: {e}")
    
    await streamer.start()


@app_ws.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    await streamer.stop()


@app_ws.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, channel: str = "global"):
    """
    Main WebSocket endpoint.
    
    Connect: ws://localhost:8001/ws?channel=global
    
    Channels:
    - global: All data
    - portfolio: Portfolio updates only
    - prices: Price updates only
    - agents: Agent status only
    
    Messages sent:
    {
        "type": "portfolio_update" | "price_update" | "agent_update" | "ping",
        "data": {...},
        "timestamp": "ISO timestamp"
    }
    """
    await manager.connect(websocket, channel)
    
    # Send initial state
    try:
        await websocket.send_json({
            "type": "connected",
            "channel": channel,
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to KEOTrading WebSocket"
        })
        
        # Send current state immediately
        if channel in ["global", "portfolio"]:
            portfolio = await streamer._fetch_portfolio()
            await websocket.send_json({
                "type": "portfolio_update",
                "data": portfolio,
                "timestamp": datetime.now().isoformat()
            })
        
        if channel in ["global", "prices"]:
            prices = await streamer._fetch_prices(['BTC/USDT', 'ETH/USDT', 'SOL/USDT'])
            await websocket.send_json({
                "type": "price_update",
                "data": prices,
                "timestamp": datetime.now().isoformat()
            })
        
        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_text()
            
            # Handle ping
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            
            # Handle subscribe
            elif data.startswith("subscribe:"):
                new_channel = data.split(":", 1)[1]
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": new_channel,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Handle unsubscribe
            elif data.startswith("unsubscribe:"):
                old_channel = data.split(":", 1)[1]
                await websocket.send_json({
                    "type": "unsubscribed",
                    "channel": old_channel,
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, channel)


@app_ws.get("/ws/status")
async def ws_status():
    """Get WebSocket server status."""
    return {
        "status": "running",
        "channels": list(manager.channels.keys()),
        "connections": sum(len(clients) for clients in manager.channels.values()),
        "streaming": streamer._running
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_ws, host="0.0.0.0", port=8001)
