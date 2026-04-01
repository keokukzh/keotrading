"""
Data Agent - Base class for data collection agents.
"""

import asyncio
import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any, Optional

from ...orchestrator.agent_manager import AgentConfig
from ...orchestrator.communicator import Communicator, Message, MessagePriority
from .base_agent import AgentMetrics, BaseAgent

logger = logging.getLogger(__name__)


class DataAgent(BaseAgent):
    """
    Base class for data collection agents.
    
    Data agents are responsible for:
    - Collecting market data (prices, orderbooks, volume, sentiment)
    - Processing and normalizing data
    - Distributing data to other agents
    - Maintaining data caches
    
    Inherited by:
    - PriceMonitor
    - OrderbookAnalyzer
    - SentimentTracker
    - VolumeAnalyzer
    """
    
    def __init__(
        self,
        config: AgentConfig,
        communicator: Communicator,
        data_interval: float = 1.0,
    ) -> None:
        """
        Initialize the DataAgent.
        
        Args:
            config: Agent configuration.
            communicator: Communicator for messaging.
            data_interval: Interval in seconds between data collection.
        """
        super().__init__(config, communicator)
        self._data_interval = data_interval
        self._data_cache: dict[str, Any] = {}
        self._collection_task: Optional[asyncio.Task] = None
        self._symbols: list[str] = []
    
    @abstractmethod
    async def collect_data(self) -> dict[str, Any]:
        """
        Collect data from external sources.
        
        Returns:
            Dictionary of collected data keyed by symbol or data type.
        """
        pass
    
    @abstractmethod
    async def process_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process and normalize collected data.
        
        Args:
            raw_data: Raw data from collection.
            
        Returns:
            Processed data dictionary.
        """
        pass
    
    async def on_start(self) -> None:
        """Start data collection."""
        # Subscribe to relevant channels
        await self.subscribe("data")
        await self.subscribe("system")
        
        # Start collection task
        self._collection_task = asyncio.create_task(self._collection_loop())
        
        self.log_info(f"DataAgent started with interval={self._data_interval}s")
    
    async def on_stop(self) -> None:
        """Stop data collection."""
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        self.log_info("DataAgent stopped")
    
    async def on_message(self, message: Message) -> None:
        """Handle incoming messages."""
        if message.message_type == "subscribe":
            # Handle subscription requests
            symbols = message.payload.get("symbols", [])
            self._symbols = symbols
            self.log_info(f"Subscribed to symbols: {symbols}")
        
        elif message.message_type == "refresh":
            # Force immediate data refresh
            await self._collect_and_broadcast()
    
    async def _collection_loop(self) -> None:
        """Main data collection loop."""
        while self._state.value != "stopped":
            try:
                await asyncio.sleep(self._data_interval)
                await self._collect_and_broadcast()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log_error(f"Collection error: {e}")
                self.increment_errors()
    
    async def _collect_and_broadcast(self) -> None:
        """Collect data, process it, and broadcast to interested agents."""
        try:
            # Collect raw data
            raw_data = await self.collect_data()
            
            # Process data
            processed_data = await self.process_data(raw_data)
            
            # Update cache
            self._data_cache.update(processed_data)
            
            # Broadcast processed data
            await self.broadcast(
                channel=self._get_data_channel(),
                message_type="data_update",
                payload={
                    "agent_id": self.agent_id,
                    "data": processed_data,
                    "timestamp": datetime.utcnow().timestamp(),
                },
                priority=MessagePriority.NORMAL,
            )
            
            self.increment_tasks()
            
        except Exception as e:
            self.log_error(f"Error in collect_and_broadcast: {e}")
            self.increment_errors()
    
    def _get_data_channel(self) -> str:
        """
        Get the channel name for this data type.
        
        Override in subclasses to specify different channels.
        """
        return "data"
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """
        Get cached data by key.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None.
        """
        return self._data_cache.get(key)
    
    def set_symbols(self, symbols: list[str]) -> None:
        """
        Set the symbols to monitor.
        
        Args:
            symbols: List of trading symbols.
        """
        self._symbols = symbols
