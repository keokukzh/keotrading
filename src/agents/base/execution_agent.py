"""
Execution Agent - Base class for order execution agents.
"""

import asyncio
import logging
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from ...orchestrator.agent_manager import AgentConfig
from ...orchestrator.communicator import Communicator, Message, MessagePriority
from ...orchestrator.risk_enforcer import RiskEnforcer, TradeRequest
from .base_agent import AgentMetrics, BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class ExecutionOrder:
    """Order to be executed."""
    order_id: str
    symbol: str
    side: str
    order_type: str  # "market", "limit", "stop_loss", "take_profit"
    size: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    leverage: float = 1.0
    exchange: str = "default"
    metadata: dict[str, Any] = None
    
    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExecutionResult:
    """Result of an order execution."""
    order_id: str
    success: bool
    executed_size: float
    executed_price: float
    commission: float = 0.0
    error: Optional[str] = None
    timestamp: float = 0.0
    
    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = datetime.utcnow().timestamp()


class ExecutionAgent(BaseAgent):
    """
    Base class for order execution agents.
    
    Execution agents are responsible for:
    - Executing orders on exchanges (CEX/DEX)
    - Managing order lifecycle
    - Tracking fill prices and commissions
    - Reporting execution results
    
    Inherited by:
    - CEXExecutor
    - DEXExecutor
    - FlashLoanCoordinator
    """
    
    def __init__(
        self,
        config: AgentConfig,
        communicator: Communicator,
        risk_enforcer: RiskEnforcer,
    ) -> None:
        """
        Initialize the ExecutionAgent.
        
        Args:
            config: Agent configuration.
            communicator: Communicator for messaging.
            risk_enforcer: RiskEnforcer for trade recording.
        """
        super().__init__(config, communicator)
        self._risk_enforcer = risk_enforcer
        self._pending_orders: dict[str, ExecutionOrder] = {}
        self._execution_task: Optional[asyncio.Task] = None
        self._exchange_name: str = "default"
    
    @abstractmethod
    async def _execute_order_internal(
        self,
        order: ExecutionOrder,
    ) -> ExecutionResult:
        """
        Internal method to execute an order on the exchange.
        
        Override in subclasses to implement exchange-specific logic.
        
        Args:
            order: Order to execute.
            
        Returns:
            ExecutionResult with execution details.
        """
        pass
    
    async def on_start(self) -> None:
        """Start execution handling."""
        await self.subscribe("strategy")
        await self.subscribe("trades")
        
        # Start execution processing task
        self._execution_task = asyncio.create_task(self._execution_loop())
        
        self.log_info(f"ExecutionAgent {self._config.name} started on {self._exchange_name}")
    
    async def on_stop(self) -> None:
        """Stop execution handling."""
        # Cancel pending orders
        for order_id in list(self._pending_orders.keys()):
            await self._cancel_order(order_id)
        
        if self._execution_task:
            self._execution_task.cancel()
            try:
                await self._execution_task
            except asyncio.CancelledError:
                pass
        
        self.log_info(f"ExecutionAgent {self._config.name} stopped")
    
    async def on_message(self, message: Message) -> None:
        """Handle incoming messages."""
        if message.message_type == "execute_signal":
            # Handle new execution request
            signal = message.payload.get("signal", {})
            risk_validation = message.payload.get("risk_validation", {})
            
            await self._handle_execution_request(signal, risk_validation)
        
        elif message.message_type == "cancel_order":
            order_id = message.payload.get("order_id")
            if order_id:
                await self._cancel_order(order_id)
        
        elif message.message_type == "cancel_all":
            await self._cancel_all_orders()
    
    async def _handle_execution_request(
        self,
        signal: dict[str, Any],
        risk_validation: dict[str, Any],
    ) -> None:
        """Handle an execution request from a strategy agent."""
        try:
            # Create execution order
            order = ExecutionOrder(
                order_id=f"{self.agent_id}_{datetime.utcnow().timestamp()}",
                symbol=signal.get("symbol"),
                side=signal.get("side"),
                order_type="market",
                size=risk_validation.get("adjusted_size", signal.get("size", 0)),
                entry_price=signal.get("entry_price"),
                stop_loss=signal.get("stop_loss"),
                take_profit=signal.get("take_profit"),
                leverage=risk_validation.get("adjusted_leverage", 1.0),
                metadata={
                    "signal": signal,
                    "risk_validation": risk_validation,
                    "strategy_agent": signal.get("agent_id", "unknown"),
                },
            )
            
            # Store pending order
            self._pending_orders[order.order_id] = order
            
            # Execute order
            result = await self._execute_order_internal(order)
            
            # Remove from pending
            self._pending_orders.pop(order.order_id, None)
            
            # Record with risk enforcer
            if result.success:
                trade_request = TradeRequest(
                    agent_id=signal.get("agent_id", "unknown"),
                    symbol=order.symbol,
                    side=order.side,
                    size=result.executed_size,
                    price=result.executed_price,
                    leverage=order.leverage,
                    stop_loss=order.stop_loss,
                    take_profit=order.take_profit,
                    request_id=order.order_id,
                )
                await self._risk_enforcer.approve_trade(trade_request)
                
                # Broadcast execution result
                await self.broadcast(
                    channel="trades",
                    message_type="order_executed",
                    payload={
                        "order": {
                            "order_id": order.order_id,
                            "symbol": order.symbol,
                            "side": order.side,
                            "size": result.executed_size,
                            "price": result.executed_price,
                            "commission": result.commission,
                        },
                        "strategy_agent": signal.get("agent_id"),
                        "timestamp": result.timestamp,
                    },
                    priority=MessagePriority.NORMAL,
                )
            else:
                # Broadcast execution failure
                await self.broadcast(
                    channel="trades",
                    message_type="order_failed",
                    payload={
                        "order_id": order.order_id,
                        "symbol": order.symbol,
                        "error": result.error,
                        "strategy_agent": signal.get("agent_id"),
                    },
                    priority=MessagePriority.HIGH,
                )
            
            self.increment_tasks()
            
        except Exception as e:
            self.log_error(f"Error handling execution request: {e}")
            self.increment_errors()
    
    async def _execute_order(
        self,
        order: ExecutionOrder,
    ) -> ExecutionResult:
        """
        Execute an order with common pre/post processing.
        
        Args:
            order: Order to execute.
            
        Returns:
            ExecutionResult.
        """
        self.log_info(
            f"Executing order: {order.order_id} {order.side} {order.size} {order.symbol}"
        )
        
        try:
            result = await self._execute_order_internal(order)
            
            if result.success:
                self.log_info(
                    f"Order executed: {order.order_id} @ {result.executed_price} "
                    f"(size: {result.executed_size}, commission: {result.commission})"
                )
            else:
                self.log_error(f"Order failed: {order.order_id} - {result.error}")
            
            return result
            
        except Exception as e:
            self.log_error(f"Order execution exception: {order.order_id} - {e}")
            return ExecutionResult(
                order_id=order.order_id,
                success=False,
                executed_size=0,
                executed_price=0,
                error=str(e),
            )
    
    async def _cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id: ID of the order to cancel.
            
        Returns:
            True if cancelled, False if not found.
        """
        if order_id not in self._pending_orders:
            return False
        
        order = self._pending_orders[order_id]
        self._pending_orders.pop(order_id)
        
        await self.broadcast(
            channel="trades",
            message_type="order_cancelled",
            payload={
                "order_id": order_id,
                "symbol": order.symbol,
            },
            priority=MessagePriority.NORMAL,
        )
        
        return True
    
    async def _cancel_all_orders(self) -> int:
        """Cancel all pending orders."""
        count = len(self._pending_orders)
        for order_id in list(self._pending_orders.keys()):
            await self._cancel_order(order_id)
        
        self.log_info(f"Cancelled {count} pending orders")
        return count
    
    async def _execution_loop(self) -> None:
        """Main execution loop (for monitoring/cleanup)."""
        while self._state.value != "stopped":
            try:
                # Monitor pending orders
                await asyncio.sleep(5)
                
                # Check for stale orders
                now = datetime.utcnow().timestamp()
                stale_orders = [
                    order_id
                    for order_id, order in self._pending_orders.items()
                    if now - order.metadata.get("timestamp", now) > 300  # 5 min timeout
                ]
                
                for order_id in stale_orders:
                    self.log_warning(f"Cancelling stale order: {order_id}")
                    await self._cancel_order(order_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log_error(f"Execution loop error: {e}")
                self.increment_errors()
    
    def get_pending_orders(self) -> dict[str, ExecutionOrder]:
        """Get all pending orders."""
        return dict(self._pending_orders)
    
    @property
    def exchange_name(self) -> str:
        """Get the exchange name."""
        return self._exchange_name
