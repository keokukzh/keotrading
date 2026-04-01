"""
Arbitrage Execution Engine
==========================

Multi-threaded order execution with timeout and cancel mechanism.
Supports intra-exchange parallel execution and inter-exchange sequential execution.
"""

import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable
from queue import Queue, Empty
import uuid

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of an execution attempt."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExchangeType(Enum):
    """Type of exchange."""
    CEX = "cex"  # Centralized exchange
    DEX = "dex"  # Decentralized exchange (blockchain)


@dataclass
class OrderRequest:
    """Request for a single order."""
    order_id: str
    exchange: str
    exchange_type: ExchangeType
    pair: str
    side: str  # "buy" or "sell"
    amount: float
    price: Optional[float] = None  # None for market orders
    callback: Optional[Callable] = None
    
    def __post_init__(self):
        if not self.order_id:
            self.order_id = str(uuid.uuid4())


@dataclass
class OrderResult:
    """Result of an order execution."""
    order_id: str
    status: ExecutionStatus
    exchange: str
    pair: str
    side: str
    requested_amount: float
    executed_amount: float
    executed_price: Optional[float]
    fee: float
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    blockchain_tx_hash: Optional[str] = None


@dataclass
class ArbitrageExecution:
    """Complete arbitrage execution with multiple legs."""
    execution_id: str
    path: list[str]  # Pool/pair IDs in order
    legs: list[OrderResult]
    total_profit: float
    total_fees: float
    status: ExecutionStatus
    start_time: float
    end_time: Optional[float] = None
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000


class ExecutionTimeout(Exception):
    """Raised when execution times out."""
    pass


class ExecutionCancelled(Exception):
    """Raised when execution is cancelled."""
    pass


class IntraExchangeExecutor:
    """
    Executes orders in parallel within the same exchange.
    Used for triangle arbitrage on a single CEX.
    """
    
    def __init__(self, exchange_name: str, max_workers: int = 3):
        """
        Initialize intra-exchange executor.
        
        Args:
            exchange_name: Name of the exchange
            max_workers: Maximum parallel orders
        """
        self.exchange_name = exchange_name
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._active_orders: dict[str, Future] = {}
        self._lock = threading.Lock()
        
        logger.info(f"Initialized IntraExchangeExecutor for {exchange_name}")
    
    def execute_parallel(
        self,
        orders: list[OrderRequest],
        timeout_seconds: float = 30.0,
    ) -> list[OrderResult]:
        """
        Execute multiple orders in parallel on the same exchange.
        
        Args:
            orders: List of orders to execute
            timeout_seconds: Maximum time to wait
            
        Returns:
            List of order results
        """
        logger.info(
            f"Executing {len(orders)} orders in parallel on {self.exchange_name}"
        )
        
        start_time = time.time()
        results: list[OrderResult] = []
        
        # Submit all orders
        futures = {}
        for order in orders:
            future = self.executor.submit(self._execute_single_order, order)
            futures[future] = order
            with self._lock:
                self._active_orders[order.order_id] = future
        
        # Wait for all to complete (or timeout)
        remaining_timeout = timeout_seconds
        
        for future, order in futures.items():
            try:
                # Calculate remaining timeout
                elapsed = time.time() - start_time
                remaining_timeout = max(timeout_seconds - elapsed, 0.1)
                
                result = future.result(timeout=remaining_timeout)
                results.append(result)
                
                logger.info(
                    f"Order {order.order_id} completed: "
                    f"amount={result.executed_amount}, price={result.executed_price}"
                )
                
            except TimeoutError:
                logger.warning(f"Order {order.order_id} timed out")
                results.append(OrderResult(
                    order_id=order.order_id,
                    status=ExecutionStatus.TIMEOUT,
                    exchange=order.exchange,
                    pair=order.pair,
                    side=order.side,
                    requested_amount=order.amount,
                    executed_amount=0.0,
                    executed_price=None,
                    fee=0.0,
                    error="Order timed out",
                    execution_time_ms=(time.time() - start_time) * 1000,
                ))
                
            except Exception as e:
                logger.error(f"Order {order.order_id} failed: {e}")
                results.append(OrderResult(
                    order_id=order.order_id,
                    status=ExecutionStatus.FAILED,
                    exchange=order.exchange,
                    pair=order.pair,
                    side=order.side,
                    requested_amount=order.amount,
                    executed_amount=0.0,
                    executed_price=None,
                    fee=0.0,
                    error=str(e),
                    execution_time_ms=(time.time() - start_time) * 1000,
                ))
            finally:
                with self._lock:
                    self._active_orders.pop(order.order_id, None)
        
        return results
    
    def _execute_single_order(self, order: OrderRequest) -> OrderResult:
        """Execute a single order (mock implementation)."""
        # In real implementation, this would call the exchange API
        start_time = time.time()
        
        # Simulate order execution
        # CEX orders are typically fast (milliseconds)
        time.sleep(0.01)  # Simulate network latency
        
        executed_price = order.price if order.price else 100.0  # Mock price
        executed_amount = order.amount * 0.999  # Small slippage
        fee = order.amount * 0.001  # 0.1% fee
        
        return OrderResult(
            order_id=order.order_id,
            status=ExecutionStatus.COMPLETED,
            exchange=order.exchange,
            pair=order.pair,
            side=order.side,
            requested_amount=order.amount,
            executed_amount=executed_amount,
            executed_price=executed_price,
            fee=fee,
            execution_time_ms=(time.time() - start_time) * 1000,
        )
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an active order.
        
        Args:
            order_id: ID of order to cancel
            
        Returns:
            True if cancelled, False if not found
        """
        with self._lock:
            future = self._active_orders.get(order_id)
            if future:
                future.cancel()
                logger.info(f"Cancelled order {order_id}")
                return True
        return False
    
    def cancel_all(self) -> int:
        """
        Cancel all active orders.
        
        Returns:
            Number of orders cancelled
        """
        count = 0
        with self._lock:
            for order_id in list(self._active_orders.keys()):
                future = self._active_orders[order_id]
                if future.cancel():
                    count += 1
                    logger.info(f"Cancelled order {order_id}")
        return count
    
    def shutdown(self, wait: bool = True):
        """Shutdown the executor."""
        logger.info(f"Shutting down IntraExchangeExecutor for {self.exchange_name}")
        self.executor.shutdown(wait=wait)


class InterExchangeExecutor:
    """
    Executes orders sequentially across different exchanges.
    Waits for blockchain confirmation between DEX operations.
    """
    
    def __init__(
        self,
        default_timeout_seconds: float = 30.0,
        blockchain_confirmations: int = 1,
    ):
        """
        Initialize inter-exchange executor.
        
        Args:
            default_timeout_seconds: Default timeout for each leg
            blockchain_confirmations: Number of confirmations to wait for DEX
        """
        self.default_timeout = default_timeout_seconds
        self.blockchain_confirmations = blockchain_confirmations
        self._exchange_executors: dict[str, IntraExchangeExecutor] = {}
        
        logger.info(
            f"Initialized InterExchangeExecutor, timeout={default_timeout}s, "
            f"confirmations={blockchain_confirmations}"
        )
    
    def get_executor(self, exchange_name: str) -> IntraExchangeExecutor:
        """Get or create executor for an exchange."""
        if exchange_name not in self._exchange_executors:
            self._exchange_executors[exchange_name] = IntraExchangeExecutor(
                exchange_name
            )
        return self._exchange_executors[exchange_name]
    
    def execute_sequential(
        self,
        legs: list[OrderRequest],
        timeout_seconds: Optional[float] = None,
    ) -> list[OrderResult]:
        """
        Execute orders sequentially across exchanges.
        
        For CEX -> CEX: Direct execution
        For DEX operations: Wait for blockchain confirmation
        
        Args:
            legs: List of orders to execute in sequence
            timeout_seconds: Total timeout (None = use default)
            
        Returns:
            List of order results
        """
        if timeout_seconds is None:
            timeout_seconds = self.default_timeout * len(legs)
        
        logger.info(
            f"Executing {len(legs)} legs sequentially, total timeout={timeout_seconds}s"
        )
        
        start_time = time.time()
        results: list[OrderResult] = []
        
        for i, leg in enumerate(legs):
            # Check timeout
            elapsed = time.time() - start_time
            remaining = timeout_seconds - elapsed
            
            if remaining <= 0:
                logger.warning(f"Timeout reached at leg {i + 1}")
                results.append(OrderResult(
                    order_id=leg.order_id,
                    status=ExecutionStatus.TIMEOUT,
                    exchange=leg.exchange,
                    pair=leg.pair,
                    side=leg.side,
                    requested_amount=leg.amount,
                    executed_amount=0.0,
                    executed_price=None,
                    fee=0.0,
                    error="Total execution timeout",
                    execution_time_ms=elapsed * 1000,
                ))
                break
            
            # Execute this leg
            leg_timeout = min(remaining, self.default_timeout)
            executor = self.get_executor(leg.exchange)
            
            # For DEX, need to wait for blockchain confirmation
            if leg.exchange_type == ExchangeType.DEX:
                logger.info(f"Leg {i + 1}: Waiting for blockchain confirmation...")
                # In real implementation, this would poll for confirmations
                time.sleep(0.5 * self.blockchain_confirmations)
            
            result = self._execute_single_leg(leg, leg_timeout)
            results.append(result)
            
            if result.status != ExecutionStatus.COMPLETED:
                logger.warning(
                    f"Leg {i + 1} failed: {result.error}, aborting sequence"
                )
                break
            
            logger.info(
                f"Leg {i + 1} completed: {leg.exchange} {leg.pair} "
                f"amount={result.executed_amount}"
            )
        
        return results
    
    def _execute_single_leg(
        self,
        leg: OrderRequest,
        timeout: float,
    ) -> OrderResult:
        """Execute a single leg with timeout."""
        start_time = time.time()
        
        # Use thread for timeout handling
        result_holder: list = [None]
        error_holder: list = [None]
        
        def execute():
            try:
                # Simulate execution
                # For real implementation, call exchange API
                time.sleep(0.05)  # Simulate execution time
                
                executed_price = leg.price if leg.price else 100.0
                executed_amount = leg.amount * 0.999
                fee = leg.amount * 0.001
                
                result_holder[0] = OrderResult(
                    order_id=leg.order_id,
                    status=ExecutionStatus.COMPLETED,
                    exchange=leg.exchange,
                    pair=leg.pair,
                    side=leg.side,
                    requested_amount=leg.amount,
                    executed_amount=executed_amount,
                    executed_price=executed_price,
                    fee=fee,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    blockchain_tx_hash=f"0x{uuid.uuid4().hex[:16]}",
                )
            except Exception as e:
                error_holder[0] = e
        
        thread = threading.Thread(target=execute)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            logger.warning(f"Leg {leg.order_id} timed out after {timeout}s")
            return OrderResult(
                order_id=leg.order_id,
                status=ExecutionStatus.TIMEOUT,
                exchange=leg.exchange,
                pair=leg.pair,
                side=leg.side,
                requested_amount=leg.amount,
                executed_amount=0.0,
                executed_price=None,
                fee=0.0,
                error=f"Execution timeout after {timeout}s",
                execution_time_ms=timeout * 1000,
            )
        
        if error_holder[0]:
            return OrderResult(
                order_id=leg.order_id,
                status=ExecutionStatus.FAILED,
                exchange=leg.exchange,
                pair=leg.pair,
                side=leg.side,
                requested_amount=leg.amount,
                executed_amount=0.0,
                executed_price=None,
                fee=0.0,
                error=str(error_holder[0]),
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        
        return result_holder[0]
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an execution across all exchanges."""
        logger.info(f"Cancelling execution {execution_id}")
        cancelled = 0
        for executor in self._exchange_executors.values():
            cancelled += executor.cancel_all()
        return cancelled > 0
    
    def shutdown(self):
        """Shutdown all executors."""
        logger.info("Shutting down InterExchangeExecutor")
        for executor in self._exchange_executors.values():
            executor.shutdown()


class ArbitrageExecutionEngine:
    """
    High-level arbitrage execution engine.
    Coordinates between intra and inter-exchange execution.
    """
    
    def __init__(
        self,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize the execution engine.
        
        Args:
            timeout_seconds: Default timeout for arbitrage executions
            max_retries: Maximum retry attempts on failure
        """
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.intra_executor = InterExchangeExecutor(
            default_timeout_seconds=timeout_seconds
        )
        self._active_executions: dict[str, ArbitrageExecution] = {}
        self._lock = threading.Lock()
        
        logger.info(f"Initialized ArbitrageExecutionEngine, timeout={timeout}s")
    
    def execute_arbitrage(
        self,
        path: list[str],
        legs: list[OrderRequest],
        execution_id: Optional[str] = None,
    ) -> ArbitrageExecution:
        """
        Execute a complete arbitrage trade.
        
        Args:
            path: List of pool/pair IDs
            legs: Order requests for each leg
            execution_id: Optional execution ID
            
        Returns:
            ArbitrageExecution with results
        """
        if execution_id is None:
            execution_id = str(uuid.uuid4())
        
        logger.info(f"Starting arbitrage execution {execution_id}: {path}")
        
        start_time = time.time()
        
        # Group legs by exchange for optimization
        # CEX legs can be parallel, DEX legs must be sequential
        cex_legs = [
            (i, leg) for i, leg in enumerate(legs)
            if leg.exchange_type == ExchangeType.CEX
        ]
        dex_legs = [
            (i, leg) for i, leg in enumerate(legs)
            if leg.exchange_type == ExchangeType.DEX
        ]
        
        results: list[Optional[OrderResult]] = [None] * len(legs)
        
        # Execute CEX legs in parallel (same exchange)
        if cex_legs:
            cex_by_exchange: dict[str, list[OrderRequest]] = {}
            for _, leg in cex_legs:
                if leg.exchange not in cex_by_exchange:
                    cex_by_exchange[leg.exchange] = []
                cex_by_exchange[leg.exchange].append(leg)
            
            for exchange, exchange_legs in cex_by_exchange.items():
                if len(exchange_legs) > 1:
                    # Parallel execution on same CEX
                    executor = self.intra_executor.get_executor(exchange)
                    parallel_results = executor.execute_parallel(
                        exchange_legs,
                        timeout_seconds=self.timeout,
                    )
                    for result in parallel_results:
                        idx = next(
                            i for i, (_, leg) in enumerate(cex_legs)
                            if leg.order_id == result.order_id
                        )
                        results[idx] = result
                else:
                    # Single leg, just execute
                    result = self._execute_single_leg(exchange_legs[0])
                    idx = next(
                        i for i, (_, leg) in enumerate(cex_legs)
                        if leg.order_id == result.order_id
                    )
                    results[idx] = result
        
        # Execute DEX legs sequentially (blockchain waits)
        if dex_legs:
            dex_legs_requests = [leg for _, leg in dex_legs]
            dex_results = self.intra_executor.execute_sequential(
                dex_legs_requests,
                timeout_seconds=self.timeout,
            )
            for result in dex_results:
                idx = next(
                    i for i, (_, leg) in enumerate(dex_legs)
                    if leg.order_id == result.order_id
                )
                results[idx] = result
        
        # Filter out None results
        valid_results = [r for r in results if r is not None]
        
        # Calculate totals
        total_profit = sum(
            r.executed_amount * 0.001 for r in valid_results  # Simplified profit calc
        )
        total_fees = sum(r.fee for r in valid_results)
        
        # Determine overall status
        if all(r.status == ExecutionStatus.COMPLETED for r in valid_results):
            status = ExecutionStatus.COMPLETED
        elif any(r.status == ExecutionStatus.TIMEOUT for r in valid_results):
            status = ExecutionStatus.TIMEOUT
        elif any(r.status == ExecutionStatus.FAILED for r in valid_results):
            status = ExecutionStatus.FAILED
        else:
            status = ExecutionStatus.RUNNING
        
        execution = ArbitrageExecution(
            execution_id=execution_id,
            path=path,
            legs=valid_results,
            total_profit=total_profit,
            total_fees=total_fees,
            status=status,
            start_time=start_time,
            end_time=time.time(),
        )
        
        with self._lock:
            self._active_executions[execution_id] = execution
        
        logger.info(
            f"Execution {execution_id} {status.value}: "
            f"profit={total_profit:.4f}, fees={total_fees:.4f}, "
            f"duration={execution.duration_ms:.1f}ms"
        )
        
        return execution
    
    def _execute_single_leg(self, leg: OrderRequest) -> OrderResult:
        """Execute a single leg."""
        start_time = time.time()
        
        # Simulate execution
        time.sleep(0.05)
        
        return OrderResult(
            order_id=leg.order_id,
            status=ExecutionStatus.COMPLETED,
            exchange=leg.exchange,
            pair=leg.pair,
            side=leg.side,
            requested_amount=leg.amount,
            executed_amount=leg.amount * 0.999,
            executed_price=leg.price or 100.0,
            fee=leg.amount * 0.001,
            execution_time_ms=(time.time() - start_time) * 1000,
        )
    
    def get_execution(self, execution_id: str) -> Optional[ArbitrageExecution]:
        """Get an execution by ID."""
        with self._lock:
            return self._active_executions.get(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution."""
        execution = self.get_execution(execution_id)
        if not execution:
            return False
        
        logger.info(f"Cancelling execution {execution_id}")
        return self.intra_executor.cancel_execution(execution_id)
    
    def shutdown(self):
        """Shutdown the execution engine."""
        logger.info("Shutting down ArbitrageExecutionEngine")
        self.intra_executor.shutdown()
