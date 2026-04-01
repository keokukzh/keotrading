"""
Communicator - Redis Pub/Sub for inter-agent communication.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Optional
import uuid

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """Inter-agent message."""
    channel: str
    sender: str
    recipient: Optional[str]  # None for broadcast
    message_type: str
    payload: dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    correlation_id: Optional[str] = None
    
    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps({
            "message_id": self.message_id,
            "channel": self.channel,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        })
    
    @classmethod
    def from_json(cls, data: str) -> "Message":
        """Deserialize message from JSON."""
        obj = json.loads(data)
        return cls(
            message_id=obj["message_id"],
            channel=obj["channel"],
            sender=obj["sender"],
            recipient=obj["recipient"],
            message_type=obj["message_type"],
            payload=obj["payload"],
            priority=MessagePriority(obj["priority"]),
            timestamp=obj["timestamp"],
            correlation_id=obj.get("correlation_id"),
        )


# Type for message handlers
MessageHandler = Callable[[Message], Coroutine[Any, Any, None]]


class Communicator:
    """
    Redis-based Pub/Sub communicator for inter-agent messaging.
    
    Supports:
    - Publish/subscribe channels
    - Direct agent-to-agent messages
    - Broadcast messages
    - Message priorities
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        agent_id: str = "system",
    ) -> None:
        """
        Initialize the Communicator.
        
        Args:
            redis_url: Redis connection URL.
            agent_id: This agent's identifier.
        """
        self._redis_url = redis_url
        self._agent_id = agent_id
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._subscriptions: dict[str, MessageHandler] = {}
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # Channel names
        self._CHANNEL_PREFIX = "keotrading:"
        self._CHANNELS = {
            "events": f"{self._CHANNEL_PREFIX}events",
            "trades": f"{self._CHANNEL_PREFIX}trades",
            "risk": f"{self._CHANNEL_PREFIX}risk",
            "data": f"{self._CHANNEL_PREFIX}data",
            "strategy": f"{self._CHANNEL_PREFIX}strategy",
            "system": f"{self._CHANNEL_PREFIX}system",
            "alerts": f"{self._CHANNEL_PREFIX}alerts",
        }
        
        logger.info(f"Communicator initialized for agent {agent_id}")
    
    async def connect(self) -> None:
        """Connect to Redis."""
        if self._redis is not None:
            return
        
        self._redis = redis.from_url(
            self._redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await self._redis.ping()
        self._pubsub = self._redis.pubsub()
        logger.info("Connected to Redis")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        self._running = False
        
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
        
        if self._redis:
            await self._redis.close()
        
        self._redis = None
        self._pubsub = None
        logger.info("Disconnected from Redis")
    
    async def publish(self, message: Message) -> int:
        """
        Publish a message to a channel.
        
        Args:
            message: Message to publish.
            
        Returns:
            Number of subscribers that received the message.
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        channel_name = f"{self._CHANNEL_PREFIX}{message.channel}"
        subscribers = await self._redis.publish(channel_name, message.to_json())
        logger.debug(f"Published to {channel_name}: {subscribers} subscribers")
        return subscribers
    
    async def subscribe(
        self,
        channel: str,
        handler: MessageHandler,
    ) -> None:
        """
        Subscribe to a channel.
        
        Args:
            channel: Channel name to subscribe to.
            handler: Async function to handle messages.
        """
        async with self._lock:
            if not self._pubsub:
                raise RuntimeError("Not connected to Redis")
            
            channel_name = f"{self._CHANNEL_PREFIX}{channel}"
            await self._pubsub.subscribe(channel_name)
            self._subscriptions[channel] = handler
            logger.info(f"Subscribed to channel: {channel}")
    
    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribe from a channel.
        
        Args:
            channel: Channel name to unsubscribe from.
        """
        async with self._lock:
            if not self._pubsub:
                return
            
            channel_name = f"{self._CHANNEL_PREFIX}{channel}"
            await self._pubsub.unsubscribe(channel_name)
            self._subscriptions.pop(channel, None)
            logger.info(f"Unsubscribed from channel: {channel}")
    
    async def send_direct(
        self,
        recipient: str,
        message_type: str,
        payload: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        Send a direct message to a specific agent.
        
        Args:
            recipient: Recipient agent ID.
            message_type: Type of message.
            payload: Message payload.
            priority: Message priority.
            correlation_id: Optional correlation ID for request/response.
            
        Returns:
            Message ID.
        """
        message = Message(
            channel=f"direct:{recipient}",
            sender=self._agent_id,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id,
        )
        await self.publish(message)
        return message.message_id
    
    async def broadcast(
        self,
        channel: str,
        message_type: str,
        payload: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> str:
        """
        Broadcast a message to all agents on a channel.
        
        Args:
            channel: Channel to broadcast on.
            message_type: Type of message.
            payload: Message payload.
            priority: Message priority.
            
        Returns:
            Message ID.
        """
        message = Message(
            channel=channel,
            sender=self._agent_id,
            recipient=None,
            message_type=message_type,
            payload=payload,
            priority=priority,
        )
        await self.publish(message)
        return message.message_id
    
    async def start_listening(self) -> None:
        """Start the message listener loop."""
        if not self._pubsub:
            raise RuntimeError("Not connected to Redis")
        
        self._running = True
        self._listener_task = asyncio.create_task(self._listener_loop())
        logger.info("Message listener started")
    
    async def _listener_loop(self) -> None:
        """Main listener loop for processing messages."""
        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message and message["type"] == "message":
                    await self._handle_message(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in listener loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _handle_message(self, raw_message: dict) -> None:
        """Handle an incoming Redis message."""
        try:
            data = raw_message["data"]
            channel = raw_message["channel"]
            
            # Extract channel name without prefix
            channel_name = channel.replace(self._CHANNEL_PREFIX, "")
            
            # Check for direct message recipient
            message = Message.from_json(data)
            
            # Skip messages addressed to other agents
            if message.recipient and message.recipient != self._agent_id:
                return
            
            # Find handler for this channel
            handler = self._subscriptions.get(channel_name)
            if handler:
                await handler(message)
            else:
                # Also check for direct message handlers
                direct_channel = f"direct:{self._agent_id}"
                handler = self._subscriptions.get(direct_channel)
                if handler:
                    await handler(message)
                    
        except Exception as e:
            logger.exception(f"Error handling message: {e}")
    
    @property
    def channels(self) -> dict[str, str]:
        """Get predefined channel names."""
        return self._CHANNELS.copy()
    
    @property
    def agent_id(self) -> str:
        """Get this agent's ID."""
        return self._agent_id
