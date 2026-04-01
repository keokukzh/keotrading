"""
Base Agent - Abstract base class for all trading agents.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from ...orchestrator.agent_manager import AgentConfig, AgentState
from ...orchestrator.communicator import Communicator, Message, MessagePriority

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Runtime metrics for an agent."""
    messages_sent: int = 0
    messages_received: int = 0
    tasks_completed: int = 0
    errors: int = 0
    last_activity: Optional[float] = None
    uptime_seconds: float = 0.0


class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.
    
    Provides common functionality:
    - Lifecycle management (start, stop, pause)
    - Message handling
    - Logging and metrics
    - Configuration access
    """
    
    def __init__(
        self,
        config: AgentConfig,
        communicator: Communicator,
    ) -> None:
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration.
            communicator: Communicator for inter-agent messaging.
        """
        self._config = config
        self._comm = communicator
        self._state = AgentState.STOPPED
        self._metrics = AgentMetrics()
        self._start_time: Optional[float] = None
        self._shutdown_event = asyncio.Event()
        self._lock = asyncio.Lock()
        
        # Set up agent-specific logger
        self._logger = logging.getLogger(f"agent.{config.agent_type}.{config.agent_id}")
        
        self._logger.info(f"Agent {config.name} ({config.agent_id}) initialized")
    
    @abstractmethod
    async def on_start(self) -> None:
        """
        Called when the agent starts. Override to perform initialization.
        
        Implementations should:
        - Subscribe to required channels
        - Initialize internal state
        - Start background tasks
        """
        pass
    
    @abstractmethod
    async def on_stop(self) -> None:
        """
        Called when the agent stops. Override to perform cleanup.
        
        Implementations should:
        - Unsubscribe from channels
        - Cancel background tasks
        - Save state if needed
        """
        pass
    
    @abstractmethod
    async def on_message(self, message: Message) -> None:
        """
        Handle an incoming message. Override to process messages.
        
        Args:
            message: The incoming message.
        """
        pass
    
    async def on_pause(self) -> None:
        """
        Called when the agent is paused. Override to pause operations.
        """
        self._logger.info(f"Agent {self._config.agent_id} paused")
    
    async def on_resume(self) -> None:
        """
        Called when the agent resumes from pause. Override to resume operations.
        """
        self._logger.info(f"Agent {self._config.agent_id} resumed")
    
    async def run(self) -> None:
        """
        Main run loop for the agent. Do not override.
        """
        try:
            self._state = AgentState.INITIALIZING
            self._start_time = datetime.utcnow().timestamp()
            
            await self.on_start()
            
            self._state = AgentState.RUNNING
            self._logger.info(f"Agent {self._config.agent_id} started")
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except Exception as e:
            self._state = AgentState.FAILED
            self._logger.exception(f"Agent {self._config.agent_id} failed: {e}")
            raise
        
        finally:
            self._state = AgentState.STOPPING
            await self.on_stop()
            self._state = AgentState.STOPPED
            self._logger.info(f"Agent {self._config.agent_id} stopped")
    
    async def shutdown(self) -> None:
        """
        Signal the agent to shut down gracefully.
        """
        self._shutdown_event.set()
    
    @property
    def agent_id(self) -> str:
        """Get the agent's ID."""
        return self._config.agent_id
    
    @property
    def agent_type(self) -> str:
        """Get the agent's type."""
        return self._config.agent_type
    
    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self._config.name
    
    @property
    def state(self) -> AgentState:
        """Get the agent's current state."""
        return self._state
    
    @property
    def metrics(self) -> AgentMetrics:
        """Get the agent's metrics."""
        return self._metrics
    
    @property
    def config(self) -> AgentConfig:
        """Get the agent's configuration."""
        return self._config
    
    async def send_message(
        self,
        recipient: str,
        message_type: str,
        payload: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> str:
        """
        Send a direct message to another agent.
        
        Args:
            recipient: Target agent ID.
            message_type: Type of message.
            payload: Message payload.
            priority: Message priority.
            
        Returns:
            Message ID.
        """
        message_id = await self._comm.send_direct(
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            priority=priority,
        )
        self._metrics.messages_sent += 1
        self._metrics.last_activity = datetime.utcnow().timestamp()
        return message_id
    
    async def broadcast(
        self,
        channel: str,
        message_type: str,
        payload: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> str:
        """
        Broadcast a message to a channel.
        
        Args:
            channel: Channel name.
            message_type: Type of message.
            payload: Message payload.
            priority: Message priority.
            
        Returns:
            Message ID.
        """
        message_id = await self._comm.broadcast(
            channel=channel,
            message_type=message_type,
            payload=payload,
            priority=priority,
        )
        self._metrics.messages_sent += 1
        self._metrics.last_activity = datetime.utcnow().timestamp()
        return message_id
    
    async def subscribe(self, channel: str) -> None:
        """
        Subscribe to a message channel.
        
        Args:
            channel: Channel name to subscribe to.
        """
        async def handler(message: Message) -> None:
            self._metrics.messages_received += 1
            self._metrics.last_activity = datetime.utcnow().timestamp()
            await self.on_message(message)
        
        await self._comm.subscribe(channel, handler)
    
    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribe from a message channel.
        
        Args:
            channel: Channel name to unsubscribe from.
        """
        await self._comm.unsubscribe(channel)
    
    def log_info(self, message: str) -> None:
        """Log an info message."""
        self._logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self._logger.warning(message)
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        self._logger.error(message)
    
    def increment_tasks(self) -> None:
        """Increment the tasks completed counter."""
        self._metrics.tasks_completed += 1
    
    def increment_errors(self) -> None:
        """Increment the errors counter."""
        self._metrics.errors += 1
