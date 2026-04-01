"""
Scheduler - Schedules and routes messages between agents.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Optional
import uuid

from .communicator import Communicator, Message, MessagePriority

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of scheduled tasks."""
    INTERVAL = "interval"  # Repeat every N seconds
    CRON = "cron"  # At specific times (simplified cron)
    DELAYED = "delayed"  # One-time delay
    ON_DEMAND = "on_demand"  # Manual trigger only


@dataclass
class ScheduledTask:
    """A scheduled task definition."""
    task_id: str
    name: str
    schedule_type: ScheduleType
    target_agent: str  # Agent to receive the message
    message_type: str  # Type of message to send
    interval_seconds: float = 0.0  # For INTERVAL type
    cron_expression: str = ""  # For CRON type (simplified)
    delay_seconds: float = 0.0  # For DELAYED type
    message_payload: dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    enabled: bool = True
    last_run: Optional[float] = None
    next_run: Optional[float] = None
    run_count: int = 0
    error_count: int = 0


class TaskHandler:
    """Handler for executing scheduled tasks."""
    
    def __call__(
        self,
        task: ScheduledTask,
    ) -> Coroutine[Any, Any, None]:
        raise NotImplementedError


class Scheduler:
    """
    Schedules and routes messages between agents.
    
    Supports:
    - Interval-based recurring tasks
    - Delayed one-time tasks
    - Message routing to agents
    - Task priority handling
    """
    
    def __init__(
        self,
        communicator: Communicator,
        max_concurrent_tasks: int = 100,
    ) -> None:
        """
        Initialize the Scheduler.
        
        Args:
            communicator: Communicator for sending messages.
            max_concurrent_tasks: Maximum concurrent task executions.
        """
        self._comm = communicator
        self._max_concurrent_tasks = max_concurrent_tasks
        self._tasks: dict[str, ScheduledTask] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        logger.info("Scheduler initialized")
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler and all tasks."""
        self._running = False
        
        # Cancel all running tasks
        for task_id in list(self._running_tasks.keys()):
            await self.cancel_task(task_id)
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Scheduler stopped")
    
    async def add_task(self, task: ScheduledTask) -> str:
        """
        Add a new scheduled task.
        
        Args:
            task: Task definition.
            
        Returns:
            Task ID.
        """
        async with self._lock:
            self._tasks[task.task_id] = task
            
            # Calculate next run time
            if task.next_run is None:
                task.next_run = self._calculate_next_run(task)
            
            logger.info(f"Task added: {task.name} ({task.task_id})")
            return task.task_id
    
    async def add_interval_task(
        self,
        name: str,
        interval_seconds: float,
        target_agent: str,
        message_type: str,
        payload: dict[str, Any] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        start_immediately: bool = False,
    ) -> str:
        """
        Add an interval-based recurring task.
        
        Args:
            name: Task name.
            interval_seconds: Interval between runs.
            target_agent: Agent to receive the message.
            message_type: Type of message to send.
            payload: Optional message payload.
            priority: Message priority.
            start_immediately: If True, run immediately on add.
            
        Returns:
            Task ID.
        """
        task = ScheduledTask(
            task_id=str(uuid.uuid4()),
            name=name,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=interval_seconds,
            target_agent=target_agent,
            message_type=message_type,
            message_payload=payload or {},
            priority=priority,
            next_run=datetime.utcnow().timestamp() if start_immediately else None,
        )
        
        return await self.add_task(task)
    
    async def add_delayed_task(
        self,
        name: str,
        delay_seconds: float,
        target_agent: str,
        message_type: str,
        payload: dict[str, Any] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> str:
        """
        Add a one-time delayed task.
        
        Args:
            name: Task name.
            delay_seconds: Delay before execution.
            target_agent: Agent to receive the message.
            message_type: Type of message to send.
            payload: Optional message payload.
            priority: Message priority.
            
        Returns:
            Task ID.
        """
        task = ScheduledTask(
            task_id=str(uuid.uuid4()),
            name=name,
            schedule_type=ScheduleType.DELAYED,
            delay_seconds=delay_seconds,
            target_agent=target_agent,
            message_type=message_type,
            message_payload=payload or {},
            priority=priority,
            next_run=datetime.utcnow().timestamp() + delay_seconds,
        )
        
        return await self.add_task(task)
    
    async def remove_task(self, task_id: str) -> bool:
        """
        Remove a scheduled task.
        
        Args:
            task_id: ID of the task to remove.
            
        Returns:
            True if task was removed, False if not found.
        """
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            # Cancel if running
            if task_id in self._running_tasks:
                self._running_tasks[task_id].cancel()
                del self._running_tasks[task_id]
            
            del self._tasks[task_id]
            logger.info(f"Task removed: {task_id}")
            return True
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: ID of the task to cancel.
            
        Returns:
            True if task was cancelled, False if not found.
        """
        async with self._lock:
            if task_id not in self._running_tasks:
                return False
            
            self._running_tasks[task_id].cancel()
            try:
                await self._running_tasks[task_id]
            except asyncio.CancelledError:
                pass
            
            del self._running_tasks[task_id]
            return True
    
    async def enable_task(self, task_id: str) -> bool:
        """Enable a task."""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            self._tasks[task_id].enabled = True
            return True
    
    async def disable_task(self, task_id: str) -> bool:
        """Disable a task."""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            self._tasks[task_id].enabled = False
            return True
    
    def _calculate_next_run(self, task: ScheduledTask) -> float:
        """Calculate next run time for a task."""
        now = datetime.utcnow().timestamp()
        
        if task.schedule_type == ScheduleType.INTERVAL:
            return now + task.interval_seconds
        elif task.schedule_type == ScheduleType.DELAYED:
            return now + task.delay_seconds
        elif task.schedule_type == ScheduleType.CRON:
            # Simplified cron: just use interval for now
            return now + task.interval_seconds
        else:
            return now
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_execute_tasks()
            except Exception as e:
                logger.exception(f"Error in scheduler loop: {e}")
            
            await asyncio.sleep(0.1)  # Check every 100ms
    
    async def _check_and_execute_tasks(self) -> None:
        """Check for tasks that need execution and run them."""
        now = datetime.utcnow().timestamp()
        
        async with self._lock:
            tasks_to_run = [
                task for task in self._tasks.values()
                if task.enabled
                and task.next_run is not None
                and now >= task.next_run
                and task.task_id not in self._running_tasks
            ]
        
        for task in tasks_to_run:
            if len(self._running_tasks) >= self._max_concurrent_tasks:
                logger.warning("Max concurrent tasks reached, skipping task")
                break
            
            self._running_tasks[task.task_id] = asyncio.create_task(
                self._execute_task(task)
            )
    
    async def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task."""
        try:
            logger.debug(f"Executing task: {task.name}")
            
            # Send message to target agent
            await self._comm.send_direct(
                recipient=task.target_agent,
                message_type=task.message_type,
                payload=task.message_payload,
                priority=task.priority,
                correlation_id=task.task_id,
            )
            
            task.last_run = datetime.utcnow().timestamp()
            task.run_count += 1
            
            # Update next run time
            if task.schedule_type in (ScheduleType.INTERVAL, ScheduleType.CRON):
                task.next_run = self._calculate_next_run(task)
            else:
                # One-time task
                async with self._lock:
                    self._tasks.pop(task.task_id, None)
            
            logger.debug(f"Task completed: {task.name}")
            
        except Exception as e:
            task.error_count += 1
            logger.exception(f"Error executing task {task.name}: {e}")
            
            # For delayed tasks, don't retry
            if task.schedule_type == ScheduleType.DELAYED:
                async with self._lock:
                    self._tasks.pop(task.task_id, None)
        
        finally:
            async with self._lock:
                self._running_tasks.pop(task.task_id, None)
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> dict[str, ScheduledTask]:
        """Get all scheduled tasks."""
        return dict(self._tasks)
    
    def get_tasks_by_agent(self, agent_id: str) -> list[ScheduledTask]:
        """Get all tasks for a specific agent."""
        return [t for t in self._tasks.values() if t.target_agent == agent_id]
    
    @property
    def running(self) -> bool:
        """Check if scheduler is running."""
        return self._running
    
    @property
    def task_count(self) -> int:
        """Get total number of tasks."""
        return len(self._tasks)
    
    @property
    def running_count(self) -> int:
        """Get number of currently running tasks."""
        return len(self._running_tasks)
