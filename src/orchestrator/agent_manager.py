"""
Agent Manager - Manages lifecycle of all trading agents.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Optional
import time
import uuid

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Lifecycle states for agents."""
    STOPPED = "stopped"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    agent_id: str
    agent_type: str
    name: str
    enabled: bool = True
    max_restarts: int = 5
    restart_delay: float = 5.0
    health_check_interval: float = 30.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInfo:
    """Runtime information about an agent."""
    agent_id: str
    config: AgentConfig
    state: AgentState = AgentState.STOPPED
    restart_count: int = 0
    last_health_check: float = 0.0
    last_start_time: float = 0.0
    error_message: Optional[str] = None
    task: Optional[asyncio.Task] = None


class AgentManager:
    """
    Manages the lifecycle of all trading agents.
    
    Handles start, stop, restart, and health checks for up to 50 agents.
    """
    
    def __init__(self, max_agents: int = 50) -> None:
        """
        Initialize the AgentManager.
        
        Args:
            max_agents: Maximum number of agents to manage.
        """
        self._max_agents = max_agents
        self._agents: dict[str, AgentInfo] = {}
        self._agent_factories: dict[str, Callable[[AgentConfig], Coroutine[Any, Any, None]]] = {}
        self._health_check_tasks: dict[str, asyncio.Task] = {}
        self._running = False
        self._lock = asyncio.Lock()
        logger.info(f"AgentManager initialized with max_agents={max_agents}")
    
    def register_factory(
        self, 
        agent_type: str, 
        factory: Callable[[AgentConfig], Coroutine[Any, Any, None]]
    ) -> None:
        """
        Register an agent factory function.
        
        Args:
            agent_type: Type identifier for the agent.
            factory: Async function that creates and runs the agent.
        """
        self._agent_factories[agent_type] = factory
        logger.debug(f"Registered factory for agent type: {agent_type}")
    
    async def add_agent(self, config: AgentConfig) -> bool:
        """
        Add a new agent to the manager.
        
        Args:
            config: Agent configuration.
            
        Returns:
            True if agent was added, False if max agents reached or duplicate.
        """
        async with self._lock:
            if len(self._agents) >= self._max_agents:
                logger.error(f"Cannot add agent {config.agent_id}: max agents reached")
                return False
            
            if config.agent_id in self._agents:
                logger.error(f"Agent {config.agent_id} already exists")
                return False
            
            if config.enabled and config.agent_type not in self._agent_factories:
                logger.error(f"No factory registered for agent type: {config.agent_type}")
                return False
            
            self._agents[config.agent_id] = AgentInfo(config=config)
            logger.info(f"Agent {config.agent_id} ({config.name}) added")
            return True
    
    async def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the manager.
        
        Args:
            agent_id: ID of the agent to remove.
            
        Returns:
            True if agent was removed, False if not found.
        """
        async with self._lock:
            if agent_id not in self._agents:
                return False
            
            await self._stop_agent(agent_id)
            del self._agents[agent_id]
            logger.info(f"Agent {agent_id} removed")
            return True
    
    async def start_agent(self, agent_id: str) -> bool:
        """
        Start a specific agent.
        
        Args:
            agent_id: ID of the agent to start.
            
        Returns:
            True if agent was started, False if not found or already running.
        """
        async with self._lock:
            if agent_id not in self._agents:
                logger.error(f"Agent {agent_id} not found")
                return False
            
            info = self._agents[agent_id]
            if info.state == AgentState.RUNNING:
                logger.warning(f"Agent {agent_id} is already running")
                return False
            
            if info.config.agent_type not in self._agent_factories:
                logger.error(f"No factory for agent type: {info.config.agent_type}")
                return False
            
            info.state = AgentState.INITIALIZING
            info.restart_count = 0
            info.error_message = None
            
            try:
                factory = self._agent_factories[info.config.agent_type]
                info.task = asyncio.create_task(factory(info.config))
                info.state = AgentState.RUNNING
                info.last_start_time = time.time()
                logger.info(f"Agent {agent_id} started")
                
                # Start health check
                self._start_health_check(agent_id)
                return True
            except Exception as e:
                info.state = AgentState.FAILED
                info.error_message = str(e)
                logger.exception(f"Failed to start agent {agent_id}")
                return False
    
    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop a specific agent.
        
        Args:
            agent_id: ID of the agent to stop.
            
        Returns:
            True if agent was stopped, False if not found.
        """
        async with self._lock:
            return await self._stop_agent(agent_id)
    
    async def _stop_agent(self, agent_id: str) -> bool:
        """Internal stop without lock acquisition."""
        if agent_id not in self._agents:
            return False
        
        info = self._agents[agent_id]
        if info.state == AgentState.STOPPED:
            return True
        
        info.state = AgentState.STOPPING
        
        # Cancel health check
        if agent_id in self._health_check_tasks:
            self._health_check_tasks[agent_id].cancel()
            del self._health_check_tasks[agent_id]
        
        # Cancel agent task
        if info.task and not info.task.done():
            info.task.cancel()
            try:
                await asyncio.wait_for(info.task, timeout=5.0)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"Error stopping agent {agent_id}: {e}")
        
        info.state = AgentState.STOPPED
        info.task = None
        logger.info(f"Agent {agent_id} stopped")
        return True
    
    async def restart_agent(self, agent_id: str) -> bool:
        """
        Restart a specific agent.
        
        Args:
            agent_id: ID of the agent to restart.
            
        Returns:
            True if agent was restarted, False if not found.
        """
        async with self._lock:
            if agent_id not in self._agents:
                return False
            
            info = self._agents[agent_id]
            
            if info.config.max_restarts > 0 and info.restart_count >= info.config.max_restarts:
                logger.error(f"Agent {agent_id} exceeded max restarts ({info.config.max_restarts})")
                info.state = AgentState.FAILED
                return False
            
            info.state = AgentState.RESTARTING
            info.restart_count += 1
            logger.info(f"Restarting agent {agent_id} (attempt {info.restart_count})")
            
            await self._stop_agent(agent_id)
            
            # Wait for restart delay
            await asyncio.sleep(info.config.restart_delay)
            
            return await self.start_agent(agent_id)
    
    async def start_all(self) -> int:
        """
        Start all enabled agents.
        
        Returns:
            Number of agents started.
        """
        count = 0
        for agent_id, info in self._agents.items():
            if info.config.enabled and info.state == AgentState.STOPPED:
                if await self.start_agent(agent_id):
                    count += 1
        logger.info(f"Started {count}/{len(self._agents)} agents")
        return count
    
    async def stop_all(self) -> int:
        """
        Stop all running agents.
        
        Returns:
            Number of agents stopped.
        """
        count = 0
        for agent_id in list(self._agents.keys()):
            if await self._stop_agent(agent_id):
                count += 1
        logger.info(f"Stopped {count} agents")
        return count
    
    def _start_health_check(self, agent_id: str) -> None:
        """Start health check loop for an agent."""
        async def health_check_loop() -> None:
            while True:
                await asyncio.sleep(self._agents[agent_id].config.health_check_interval)
                await self._check_health(agent_id)
        
        self._health_check_tasks[agent_id] = asyncio.create_task(health_check_loop())
    
    async def _check_health(self, agent_id: str) -> None:
        """Check health of a single agent."""
        async with self._lock:
            if agent_id not in self._agents:
                return
            
            info = self._agents[agent_id]
            
            if info.state != AgentState.RUNNING:
                return
            
            if info.task and info.task.done():
                try:
                    info.task.result()
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    info.error_message = str(e)
                    info.state = AgentState.FAILED
                    logger.error(f"Agent {agent_id} failed: {e}")
                    await self.restart_agent(agent_id)
                    return
            
            info.last_health_check = time.time()
    
    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """Get runtime info for an agent."""
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> dict[str, AgentInfo]:
        """Get all agent info."""
        return dict(self._agents)
    
    def get_agents_by_state(self, state: AgentState) -> list[AgentInfo]:
        """Get all agents in a specific state."""
        return [info for info in self._agents.values() if info.state == state]
    
    def get_agents_by_type(self, agent_type: str) -> list[AgentInfo]:
        """Get all agents of a specific type."""
        return [info for info in self._agents.values() if info.config.agent_type == agent_type]
    
    async def start(self) -> None:
        """Start the agent manager."""
        self._running = True
        logger.info("AgentManager started")
    
    async def stop(self) -> None:
        """Stop the agent manager and all agents."""
        self._running = False
        await self.stop_all()
        logger.info("AgentManager stopped")
    
    @property
    def running(self) -> bool:
        """Check if manager is running."""
        return self._running
    
    @property
    def agent_count(self) -> int:
        """Get current number of agents."""
        return len(self._agents)
    
    @property
    def running_count(self) -> int:
        """Get number of running agents."""
        return len(self.get_agents_by_state(AgentState.RUNNING))
