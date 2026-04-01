"""
KEOTrading Multi-Agent Trading System
=====================================
Multi-agent orchestration for trading with defined roles and task lifecycle.

Based on agent-team-orchestration skill patterns.

AGENT ROLES:
- Orchestrator: Routes tasks, tracks state, makes decisions
- Signal Analyzer: Market data, patterns, signals
- Risk Manager: Risk limits, stop-loss, position sizing
- Trade Executor: Executes orders, checks fills
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task lifecycle states."""
    INBOX = "inbox"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    """A trading task with lifecycle tracking."""
    id: str
    type: str  # signal_analysis, risk_check, order_execution
    description: str
    status: TaskStatus = TaskStatus.INBOX
    assigned_to: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    priority: int = 0  # 0 = low, 1 = medium, 2 = high, 3 = urgent
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "status": self.status.value,
        }


@dataclass
class Agent:
    """A trading agent with defined role."""
    id: str
    name: str
    role: str  # orchestrator, signal_analyzer, risk_manager, trade_executor
    status: str = "idle"  # idle, working, error
    capabilities: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    last_heartbeat: str = ""
    model: str = "gpt-4"  # Default model
    
    def __post_init__(self):
        if not self.last_heartbeat:
            self.last_heartbeat = datetime.now().isoformat()


class TradingAgentOrchestrator:
    """
    Orchestrates multi-agent trading with task lifecycle management.
    
    Task Flow:
    Inbox -> Assigned -> In Progress -> Review -> Done | Failed
    
    Agent Roles:
    - Signal Analyzer: Analyzes market data, generates signals
    - Risk Manager: Reviews signals against risk limits
    - Trade Executor: Places and manages orders
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []  # Task IDs in queue
        self.task_history_file = self.data_dir / "task_history.jsonl"
        
        self._initialize_agents()
        self._load_tasks()
    
    def _initialize_agents(self):
        """Initialize the trading agent team."""
        self.agents = {
            "orchestrator": Agent(
                id="orchestrator",
                name="Trading Orchestrator",
                role="orchestrator",
                capabilities=["task_routing", "decision_making", "portfolio_management"],
            ),
            "signal_analyzer": Agent(
                id="signal_analyzer",
                name="Signal Analyzer",
                role="signal_analyzer",
                capabilities=["market_analysis", "pattern_recognition", "signal_generation"],
            ),
            "risk_manager": Agent(
                id="risk_manager",
                name="Risk Manager",
                role="risk_manager",
                capabilities=["risk_assessment", "position_sizing", "stop_loss"],
            ),
            "trade_executor": Agent(
                id="trade_executor",
                name="Trade Executor",
                role="trade_executor",
                capabilities=["order_placement", "fill_monitoring", "slippage_check"],
            ),
        }
        logger.info(f"Initialized {len(self.agents)} trading agents")
    
    def _load_tasks(self):
        """Load tasks from history file."""
        if self.task_history_file.exists():
            try:
                with open(self.task_history_file) as f:
                    for line in f:
                        if line.strip():
                            task_data = json.loads(line)
                            task_data["status"] = TaskStatus(task_data["status"])
                            task = Task(**task_data)
                            self.tasks[task.id] = task
            except Exception as e:
                logger.error(f"Error loading tasks: {e}")
    
    def _save_task(self, task: Task):
        """Append task to history file."""
        task.updated_at = datetime.now().isoformat()
        with open(self.task_history_file, 'a') as f:
            f.write(json.dumps(task.to_dict()) + '\n')
    
    def create_task(
        self,
        task_type: str,
        description: str,
        priority: int = 1,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Create a new task and add to inbox.
        Returns task ID.
        """
        task_id = f"{task_type}_{uuid.uuid4().hex[:8]}"
        task = Task(
            id=task_id,
            type=task_type,
            description=description,
            priority=priority,
            metadata=metadata or {},
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        self._prioritize_queue()
        self._save_task(task)
        
        logger.info(f"Created task {task_id}: {description}")
        return task_id
    
    def _prioritize_queue(self):
        """Sort task queue by priority (high first)."""
        self.task_queue.sort(
            key=lambda tid: self.tasks[tid].priority,
            reverse=True
        )
    
    def get_next_task(self, agent_id: str) -> Optional[Task]:
        """Get next available task for an agent."""
        for task_id in self.task_queue:
            task = self.tasks[task_id]
            if task.status == TaskStatus.INBOX:
                # Check if agent can handle this task type
                agent = self.agents.get(agent_id)
                if agent and task.type in agent.capabilities:
                    task.status = TaskStatus.ASSIGNED
                    task.assigned_to = agent_id
                    agent.current_task = task_id
                    agent.status = "working"
                    self._save_task(task)
                    logger.info(f"Assigned task {task_id} to {agent_id}")
                    return task
        
        return None
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ):
        """Update task status and result."""
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return
        
        task.status = status
        task.updated_at = datetime.now().isoformat()
        
        if result:
            task.result = result
        if error:
            task.error = error
        
        # Free the agent
        if task.assigned_to:
            agent = self.agents.get(task.assigned_to)
            if agent:
                agent.current_task = None
                agent.status = "idle"
        
        self._save_task(task)
        logger.info(f"Task {task_id} -> {status.value}")
    
    def complete_task(self, task_id: str, result: Dict):
        """Mark task as done with result."""
        self.update_task_status(task_id, TaskStatus.DONE, result)
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)
    
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed with error."""
        self.update_task_status(task_id, TaskStatus.FAILED, error=error)
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)
    
    def get_agent_status(self) -> List[Dict]:
        """Get status of all agents."""
        return [
            {
                **asdict(agent),
                "current_task": agent.current_task,
                "task_status": self.tasks.get(agent.current_task).status.value 
                    if agent.current_task and self.tasks.get(agent.current_task) else None,
            }
            for agent in self.agents.values()
        ]
    
    def get_task_board(self) -> Dict[str, Any]:
        """Get task board summary."""
        summary = {
            "total": len(self.tasks),
            "by_status": {},
            "queue": [],
        }
        
        for status in TaskStatus:
            count = sum(1 for t in self.tasks.values() if t.status == status)
            summary["by_status"][status.value] = count
        
        for task_id in self.task_queue[:10]:  # Top 10
            task = self.tasks[task_id]
            summary["queue"].append({
                "id": task.id,
                "type": task.type,
                "priority": task.priority,
                "status": task.status.value,
            })
        
        return summary
    
    async def process_signal_task(self, task: Task) -> Dict:
        """Process a signal analysis task."""
        # Simulated signal analysis
        signal = {
            "action": "buy",
            "symbol": task.metadata.get("symbol", "BTC/USDT"),
            "confidence": 0.85,
            "entry_price": task.metadata.get("price", 42000),
            "stop_loss": task.metadata.get("price", 42000) * 0.98,
            "take_profit": task.metadata.get("price", 42000) * 1.05,
            "risk_level": "medium",
        }
        return signal
    
    async def process_risk_task(self, task: Task) -> Dict:
        """Process a risk check task."""
        signal = task.metadata.get("signal", {})
        
        # Simulated risk check
        risk_result = {
            "approved": True,
            "position_size": 0.1,  # % of portfolio
            "max_loss": signal.get("stop_loss", 0) * signal.get("quantity", 1),
            "risk_reward_ratio": 2.5,
            "warnings": [],
        }
        
        # Check risk limits
        if risk_result["risk_reward_ratio"] < 1.5:
            risk_result["warnings"].append("Risk/reward below 1.5")
        
        return risk_result
    
    async def process_execution_task(self, task: Task) -> Dict:
        """Process an order execution task."""
        risk = task.metadata.get("risk_result", {})
        if not risk.get("approved"):
            return {"success": False, "error": "Risk check rejected"}
        
        # Simulated order execution
        execution = {
            "success": True,
            "order_id": f"ord_{uuid.uuid4().hex[:8]}",
            "filled_price": task.metadata.get("entry_price", 42000),
            "quantity": task.metadata.get("quantity", 0.1),
            "fee": task.metadata.get("entry_price", 42000) * 0.001,
        }
        return execution
    
    async def run_task(self, task_id: str) -> Dict:
        """Run a task based on its type."""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}
        
        task.status = TaskStatus.IN_PROGRESS
        self._save_task(task)
        
        try:
            if task.type == "signal_analysis":
                result = await self.process_signal_task(task)
            elif task.type == "risk_check":
                result = await self.process_risk_task(task)
            elif task.type == "order_execution":
                result = await self.process_execution_task(task)
            else:
                result = {"error": f"Unknown task type: {task.type}"}
            
            self.complete_task(task_id, result)
            return result
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            self.fail_task(task_id, str(e))
            return {"error": str(e)}
    
    def create_trade_signal(
        self,
        symbol: str,
        action: str,
        price: float,
        quantity: float = 0.1,
    ) -> str:
        """
        Create a complete trading workflow:
        1. Signal Analysis
        2. Risk Check
        3. Order Execution
        
        Returns the signal analysis task ID.
        """
        # Create signal analysis task
        signal_task_id = self.create_task(
            task_type="signal_analysis",
            description=f"Analyze {action} signal for {symbol}",
            priority=2,
            metadata={
                "symbol": symbol,
                "action": action,
                "price": price,
                "quantity": quantity,
            },
        )
        
        # Create risk check task (will be triggered after signal)
        risk_task_id = self.create_task(
            task_type="risk_check",
            description=f"Risk check for {symbol} {action}",
            priority=1,
            metadata={
                "signal_task_id": signal_task_id,
                "symbol": symbol,
                "action": action,
                "price": price,
                "quantity": quantity,
            },
        )
        
        # Create execution task
        exec_task_id = self.create_task(
            task_type="order_execution",
            description=f"Execute {action} order for {symbol}",
            priority=0,
            metadata={
                "risk_task_id": risk_task_id,
                "symbol": symbol,
                "action": action,
                "entry_price": price,
                "quantity": quantity,
            },
        )
        
        logger.info(f"Created trade workflow: signal={signal_task_id}, risk={risk_task_id}, exec={exec_task_id}")
        return signal_task_id


# Global orchestrator instance
_orchestrator: Optional[TradingAgentOrchestrator] = None


def get_trading_orchestrator() -> TradingAgentOrchestrator:
    """Get or create trading orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TradingAgentOrchestrator()
    return _orchestrator
