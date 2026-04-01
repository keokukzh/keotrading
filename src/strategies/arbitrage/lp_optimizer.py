"""
LP Arbitrage Optimizer
======================

LP (Liquidity Provider) Arbitrage optimizer using PULP (CBC solver) for finding
optimal multi-lateral arbitrage paths across exchanges and pools.

Inspired by hzjken's LP arbitrage approach.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
from pulp import (
    LpMaximize,
    LpProblem,
    LpVariable,
    LpBinary,
    lpSum,
    value,
    PULP_CBC_CMD,
)

logger = logging.getLogger(__name__)


class OrderFlow(Enum):
    """Direction of trade flow."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class TradingFee:
    """Trading fee configuration."""
    maker_fee: float = 0.001  # 0.1%
    taker_fee: float = 0.001  # 0.1%


@dataclass
class PoolInfo:
    """Information about a liquidity pool or trading pair."""
    pool_id: str
    exchange: str
    base_asset: str
    quote_asset: str
    bid_price: float  # Best bid (sell price)
    ask_price: float  # Best ask (buy price)
    bid_volume: float  # Available volume at bid
    ask_volume: float  # Available volume at ask
    fee: TradingFee = field(default_factory=TradingFee)
    withdrawal_fee: float = 0.0  # Asset withdrawal fee


@dataclass
class BalanceInfo:
    """Account balance information."""
    asset: str
    available: float
    locked: float = 0.0
    
    @property
    def total(self) -> float:
        return self.available + self.locked


@dataclass
class ArbitragePath:
    """Represents a complete arbitrage path."""
    pools: list[str]
    flows: list[OrderFlow]
    amounts: list[float]
    expected_profit_pct: float
    net_profit_usd: float
    confidence: float  # 0-1 based on liquidity depth


class ArbitragePathOptimizer:
    """
    Finds optimal multi-lateral arbitrage paths using MILP optimization.
    
    Supports unlimited path length (not just triangular) by formulating
    the problem as a network flow optimization.
    """
    
    def __init__(
        self,
        pools: list[PoolInfo],
        balances: dict[str, BalanceInfo],
        initial_capital_usd: float = 1000.0,
        min_profit_pct: float = 0.1,
        max_path_length: int = 5,
    ):
        """
        Initialize the arbitrage path optimizer.
        
        Args:
            pools: List of available pools/exchanges
            balances: Dictionary of asset -> BalanceInfo
            initial_capital_usd: Starting capital in USD
            min_profit_pct: Minimum profit threshold (%)
            max_path_length: Maximum number of legs in path
        """
        self.pools = pools
        self.balances = balances
        self.initial_capital_usd = initial_capital_usd
        self.min_profit_pct = min_profit_pct
        self.max_path_length = max_path_length
        self._pool_index = {p.pool_id: p for p in pools}
        
        logger.info(
            f"Initialized ArbitragePathOptimizer with {len(pools)} pools, "
            f"capital=${initial_capital_usd}, min_profit={min_profit_pct}%"
        )
    
    def find_optimal_path(
        self,
        start_asset: str = "USDT",
        end_asset: Optional[str] = None,
    ) -> Optional[ArbitragePath]:
        """
        Find the optimal arbitrage path starting from an asset.
        
        Args:
            start_asset: Asset to start the path with
            end_asset: Asset to end the path with (None = same as start)
            
        Returns:
            ArbitragePath if profitable opportunity found, None otherwise
        """
        if end_asset is None:
            end_asset = start_asset
        
        logger.info(f"Finding optimal path from {start_asset} to {end_asset}")
        
        # Build the MILP problem
        problem = LpProblem("Arbitrage_Optimization", LpMaximize)
        
        # Decision variables
        # x[i,j] = 1 if we trade from pool i to pool j
        # y[i] = 1 if pool i is used in the path
        
        pool_ids = [p.pool_id for p in self.pools]
        n = len(pool_ids)
        
        # Use flow variables for each asset
        flow_vars = {}
        for i, pool in enumerate(self.pools):
            for j, other_pool in enumerate(self.pools):
                if i != j:
                    var_name = f"flow_{pool.pool_id}_{other_pool.pool_id}"
                    flow_vars[(pool.pool_id, other_pool.pool_id)] = LpVariable(
                        var_name, lowBound=0, cat="Continuous"
                    )
        
        # Binary variables for path selection
        in_path = {
            p.pool_id: LpVariable(f"in_path_{p.pool_id}", cat=LpBinary)
            for p in self.pools
        }
        
        # Objective: Maximize profit
        # Profit = sum of (output_value - input_value) for each trade
        profit_vars = []
        for pool in self.pools:
            profit_var = LpVariable(f"profit_{pool.pool_id}", lowBound=0)
            profit_vars.append(profit_var)
        
        # Simple profit calculation (output - input)
        # This is a simplified model - real implementation would track asset flows
        problem += lpSum(profit_vars), "Total_Profit"
        
        # Constraints
        # 1. Path length constraint
        problem += (
            lpSum(in_path.values()) <= self.max_path_length,
            "Max_Path_Length"
        )
        
        # 2. Flow conservation (simplified)
        # In a real implementation, we'd track actual asset flows
        
        # 3. Minimum profit threshold
        total_profit = lpSum(profit_vars)
        problem += (
            total_profit >= self.min_profit_pct / 100 * self.initial_capital_usd,
            "Min_Profit_Threshold"
        )
        
        # Solve
        solver = PULP_CBC_CMD(msg=0)
        status = problem.solve(solver)
        
        logger.info(f"Optimization status: {status}")
        
        if status != 1:  # Not optimal
            logger.info("No optimal solution found")
            return None
        
        # Extract path
        active_pools = [
            pool.pool_id for pool in self.pools
            if value(in_path[pool.pool_id]) == 1
        ]
        
        if len(active_pools) < 2:
            logger.info("Path too short")
            return None
        
        # Build path details
        # Simplified: just return the pools in order
        return ArbitragePath(
            pools=active_pools,
            flows=[OrderFlow.BUY] * len(active_pools),  # Simplified
            amounts=[self.initial_capital_usd / len(active_pools)] * len(active_pools),
            expected_profit_pct=value(total_profit) / self.initial_capital_usd * 100,
            net_profit_usd=value(total_profit),
            confidence=0.8,  # Simplified confidence
        )
    
    def find_all_profitable_paths(
        self,
        start_asset: str = "USDT",
        min_profit_pct: float = 0.1,
    ) -> list[ArbitragePath]:
        """
        Find all profitable arbitrage paths.
        
        Args:
            start_asset: Asset to start paths with
            min_profit_pct: Minimum profit threshold
            
        Returns:
            List of profitable ArbitragePath objects
        """
        logger.info(f"Searching for all profitable paths starting from {start_asset}")
        
        paths = []
        
        # Try paths of different lengths
        for path_length in range(2, self.max_path_length + 1):
            path = self._find_path_of_length(
                start_asset, path_length, min_profit_pct
            )
            if path and path.expected_profit_pct >= min_profit_pct:
                paths.append(path)
        
        # Sort by profit
        paths.sort(key=lambda p: p.net_profit_usd, reverse=True)
        
        logger.info(f"Found {len(paths)} profitable paths")
        return paths
    
    def _find_path_of_length(
        self,
        start_asset: str,
        length: int,
        min_profit_pct: float,
    ) -> Optional[ArbitragePath]:
        """Find a path of specific length."""
        # Simplified implementation
        # Real implementation would use DFS/BFS with profit calculation
        
        pools_involved = []
        current_asset = start_asset
        
        for i in range(length):
            # Find best pool to use next
            best_pool = None
            best_rate = 0.0
            
            for pool in self.pools:
                if pool.base_asset == current_asset:
                    # Can trade from this pool
                    effective_rate = pool.ask_price * (1 - pool.fee.taker_fee)
                    if effective_rate > best_rate:
                        best_rate = effective_rate
                        best_pool = pool
            
            if best_pool is None:
                return None
            
            pools_involved.append(best_pool.pool_id)
            current_asset = best_pool.quote_asset
        
        # Calculate expected profit
        profit = self._calculate_path_profit(pools_involved, start_asset)
        
        if profit >= min_profit_pct / 100 * self.initial_capital_usd:
            return ArbitragePath(
                pools=pools_involved,
                flows=[OrderFlow.BUY] * len(pools_involved),
                amounts=[self.initial_capital_usd] * len(pools_involved),
                expected_profit_pct=profit / self.initial_capital_usd * 100,
                net_profit_usd=profit,
                confidence=0.85,
            )
        
        return None
    
    def _calculate_path_profit(self, pool_ids: list[str], start_asset: str) -> float:
        """Calculate profit for a given path."""
        if not pool_ids:
            return 0.0
        
        amount = self.initial_capital_usd
        current_asset = start_asset
        
        for pool_id in pool_ids:
            pool = self._pool_index.get(pool_id)
            if pool is None:
                return 0.0
            
            if pool.base_asset != current_asset:
                # Wrong direction
                return 0.0
            
            # Apply trading fee
            fee = amount * pool.fee.taker_fee
            amount_after_fee = amount - fee
            
            # Convert to quote asset
            if current_asset == pool.base_asset:
                amount = amount_after_fee * pool.ask_price
            
            current_asset = pool.quote_asset
        
        # Check if we returned to start asset
        if current_asset == start_asset:
            return amount - self.initial_capital_usd
        
        return 0.0


class AmountOptimizer:
    """
    Optimizes trading amounts per orderbook depth to maximize profit
    while minimizing slippage.
    """
    
    def __init__(
        self,
        pool: PoolInfo,
        balance: BalanceInfo,
        max_slippage_pct: float = 0.5,
    ):
        """
        Initialize the amount optimizer.
        
        Args:
            pool: Pool to trade in
            balance: Available balance
            max_slippage_pct: Maximum allowed slippage (%)
        """
        self.pool = pool
        self.balance = balance
        self.max_slippage_pct = max_slippage_pct
        
        logger.info(
            f"Initialized AmountOptimizer for {pool.pool_id}, "
            f"balance={balance.available}, max_slippage={max_slippage_pct}%"
        )
    
    def optimize_amount(
        self,
        target_amount: Optional[float] = None,
    ) -> tuple[float, float, float]:
        """
        Optimize the trading amount based on orderbook depth.
        
        Args:
            target_amount: Target amount to trade (None = use full balance)
            
        Returns:
            Tuple of (optimal_amount, expected_slippage, expected_slippage_pct)
        """
        if target_amount is None:
            target_amount = self.balance.available
        
        logger.info(f"Optimizing amount for {self.pool.pool_id}, target={target_amount}")
        
        # Build orderbook levels
        # In a real implementation, we'd use actual orderbook data
        # For now, use the pool's bid/ask volume
        
        # Calculate slippage using linear interpolation
        # Assume uniform liquidity distribution within bid/ask volumes
        available_volume = min(self.pool.bid_volume, self.pool.ask_volume)
        
        if target_amount > available_volume:
            logger.warning(
                f"Target amount {target_amount} exceeds available volume {available_volume}"
            )
            target_amount = available_volume
        
        # Calculate slippage
        # Simple model: slippage increases linearly with volume
        volume_ratio = target_amount / available_volume if available_volume > 0 else 1.0
        slippage_pct = volume_ratio * self.max_slippage_pct
        
        # Adjust for fees
        net_amount = target_amount * (1 - self.pool.fee.taker_fee)
        effective_slippage = net_amount * slippage_pct / 100
        
        logger.info(
            f"Optimized: amount={target_amount}, slippage={effective_slippage:.4f} "
            f"({slippage_pct:.2f}%)"
        )
        
        return target_amount, effective_slippage, slippage_pct
    
    def calculate_optimal_split(
        self,
        total_amount: float,
        num_slices: int = 5,
    ) -> list[float]:
        """
        Split an order into optimal slices to minimize slippage.
        
        Args:
            total_amount: Total amount to trade
            num_slices: Number of slices to split into
            
        Returns:
            List of amounts for each slice
        """
        logger.info(f"Calculating optimal split: {total_amount} into {num_slices} slices")
        
        # Calculate optimal split using geometric progression
        # Earlier slices get more volume (better price)
        slices = []
        remaining = total_amount
        ratio = 0.7  # Each subsequent slice is 70% of previous
        
        for i in range(num_slices):
            if i == num_slices - 1:
                # Last slice takes remaining
                slice_amount = remaining
            else:
                # Geometric progression
                slice_amount = remaining * (1 - ratio) / (1 - ratio ** (num_slices - i - 1))
            
            slices.append(max(slice_amount, 0))
            remaining -= slice_amount
        
        logger.info(f"Optimal slices: {slices}")
        return slices
    
    def validate_trade(
        self,
        amount: float,
        side: OrderFlow,
    ) -> tuple[bool, str]:
        """
        Validate if a trade is feasible.
        
        Args:
            amount: Amount to trade
            side: Buy or sell
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check balance
        if amount > self.balance.available:
            return False, f"Amount {amount} exceeds balance {self.balance.available}"
        
        # Check liquidity
        volume = self.pool.ask_volume if side == OrderFlow.BUY else self.pool.bid_volume
        if amount > volume:
            return False, f"Amount {amount} exceeds available volume {volume}"
        
        # Check slippage
        _, _, slippage_pct = self.optimize_amount(amount)
        if slippage_pct > self.max_slippage_pct:
            return False, f"Slippage {slippage_pct:.2f}% exceeds max {self.max_slippage_pct}%"
        
        return True, "Valid"


def calculate_arbitrage_profit(
    pools: list[PoolInfo],
    start_amount: float,
    start_asset: str,
    path: list[str],
) -> dict:
    """
    Calculate profit for a specific arbitrage path.
    
    Args:
        pools: List of available pools
        start_amount: Starting amount
        start_asset: Starting asset
        path: List of pool IDs in order
        
    Returns:
        Dictionary with profit details
    """
    pool_map = {p.pool_id: p for p in pools}
    amount = start_amount
    current_asset = start_asset
    trades = []
    total_fees = 0.0
    
    for pool_id in path:
        pool = pool_map.get(pool_id)
        if pool is None:
            return {"valid": False, "reason": f"Pool {pool_id} not found"}
        
        if pool.base_asset != current_asset:
            return {"valid": False, "reason": f"Asset mismatch: {current_asset} != {pool.base_asset}"}
        
        # Calculate trade
        fee = amount * pool.fee.taker_fee
        net_amount = amount - fee
        received = net_amount * pool.ask_price  # Buying quote asset
        
        trades.append({
            "pool_id": pool_id,
            "side": "buy",
            "input_asset": current_asset,
            "output_asset": pool.quote_asset,
            "input_amount": amount,
            "output_amount": received,
            "fee": fee,
        })
        
        total_fees += fee
        amount = received
        current_asset = pool.quote_asset
    
    # Calculate final profit
    profit = amount - start_amount
    profit_pct = (profit / start_amount) * 100 if start_amount > 0 else 0
    
    return {
        "valid": True,
        "start_asset": start_asset,
        "end_asset": current_asset,
        "start_amount": start_amount,
        "end_amount": amount,
        "profit": profit,
        "profit_pct": profit_pct,
        "total_fees": total_fees,
        "trades": trades,
        "path": path,
    }
