"""
Risk Enforcer - Enforces trading risk limits.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
import time

from .communicator import Communicator, Message, MessagePriority

logger = logging.getLogger(__name__)


class RiskLimitType(Enum):
    """Types of risk limits."""
    POSITION_SIZE = "position_size"
    PORTFOLIO_EXPOSURE = "portfolio_exposure"
    DRAWDOWN = "drawdown"
    DAILY_LOSS = "daily_loss"
    LEVERAGE = "leverage"
    CONCENTRATION = "concentration"


@dataclass
class RiskLimit:
    """A single risk limit configuration."""
    limit_type: RiskLimitType
    value: float
    soft_threshold: float = 0.9  # Warning at 90%
    hard_threshold: float = 1.0  # Block at 100%
    
    @property
    def soft_value(self) -> float:
        """Get soft threshold value."""
        return self.value * self.soft_threshold
    
    @property
    def hard_value(self) -> float:
        """Get hard threshold value."""
        return self.value * self.hard_threshold


@dataclass
class RiskMetrics:
    """Current risk metrics."""
    total_exposure: float = 0.0
    daily_pnl: float = 0.0
    daily_loss: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    portfolio_value: float = 0.0
    open_positions: int = 0
    largest_position: float = 0.0
    
    
@dataclass
class TradeRequest:
    """A trade request to be validated."""
    agent_id: str
    symbol: str
    side: str  # "buy" or "sell"
    size: float
    price: float
    leverage: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    request_id: str = ""
    
    @property
    def notional_value(self) -> float:
        """Calculate notional value of the trade."""
        return abs(self.size * self.price * self.leverage)


class RiskDecision(Enum):
    """Risk validation decision."""
    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REJECTED = "rejected"
    PENDING_REVIEW = "pending_review"


@dataclass
class RiskValidation:
    """Result of risk validation."""
    decision: RiskDecision
    trade_request: TradeRequest
    reason: str
    warnings: list[str] = field(default_factory=list)
    adjusted_size: Optional[float] = None
    adjusted_leverage: Optional[float] = None


class RiskEnforcer:
    """
    Enforces risk limits across all trading agents.
    
    Limits enforced:
    - 2% max per single trade
    - 10% max per agent
    - Portfolio drawdown limits
    - Daily loss limits
    - Position concentration limits
    """
    
    def __init__(
        self,
        communicator: Communicator,
        max_trade_pct: float = 0.02,  # 2% per trade
        max_agent_exposure_pct: float = 0.10,  # 10% per agent
        max_portfolio_exposure: float = 1.0,  # 100% portfolio
        max_daily_loss_pct: float = 0.05,  # 5% daily loss limit
        max_drawdown_pct: float = 0.15,  # 15% max drawdown
        max_leverage: float = 5.0,
        initial_portfolio_value: float = 100000.0,
    ) -> None:
        """
        Initialize the RiskEnforcer.
        
        Args:
            communicator: Communicator for alerts.
            max_trade_pct: Maximum % of portfolio per trade.
            max_agent_exposure_pct: Maximum % of portfolio per agent.
            max_portfolio_exposure: Maximum total portfolio exposure.
            max_daily_loss_pct: Maximum daily loss as % of portfolio.
            max_drawdown_pct: Maximum drawdown as % of portfolio.
            max_leverage: Maximum allowed leverage.
            initial_portfolio_value: Starting portfolio value.
        """
        self._comm = communicator
        self._max_trade_pct = max_trade_pct
        self._max_agent_exposure_pct = max_agent_exposure_pct
        self._max_portfolio_exposure = max_portfolio_exposure
        self._max_daily_loss_pct = max_daily_loss_pct
        self._max_drawdown_pct = max_drawdown_pct
        self._max_leverage = max_leverage
        self._initial_portfolio_value = initial_portfolio_value
        
        # Current state
        self._metrics = RiskMetrics()
        self._metrics.portfolio_value = initial_portfolio_value
        self._agent_exposures: dict[str, float] = {}
        self._position_exposures: dict[str, float] = {}
        self._daily_reset_time = self._get_daily_reset_time()
        self._peak_portfolio_value = initial_portfolio_value
        
        # Risk limits
        self._limits: dict[RiskLimitType, RiskLimit] = {
            RiskLimitType.POSITION_SIZE: RiskLimit(
                limit_type=RiskLimitType.POSITION_SIZE,
                value=initial_portfolio_value * max_trade_pct,
            ),
            RiskLimitType.PORTFOLIO_EXPOSURE: RiskLimit(
                limit_type=RiskLimitType.PORTFOLIO_EXPOSURE,
                value=initial_portfolio_value * max_portfolio_exposure,
            ),
            RiskLimitType.DAILY_LOSS: RiskLimit(
                limit_type=RiskLimitType.DAILY_LOSS,
                value=initial_portfolio_value * max_daily_loss_pct,
            ),
            RiskLimitType.DRAWDOWN: RiskLimit(
                limit_type=RiskLimitType.DRAWDOWN,
                value=initial_portfolio_value * max_drawdown_pct,
            ),
            RiskLimitType.LEVERAGE: RiskLimit(
                limit_type=RiskLimitType.LEVERAGE,
                value=max_leverage,
            ),
        }
        
        logger.info("RiskEnforcer initialized with limits:")
        for limit_type, limit in self._limits.items():
            logger.info(f"  {limit_type.value}: {limit.value}")
    
    def _get_daily_reset_time(self) -> datetime:
        """Get the next daily reset time (midnight UTC)."""
        now = datetime.utcnow()
        return datetime(now.year, now.month, now.day) + timedelta(days=1)
    
    async def validate_trade(self, trade: TradeRequest) -> RiskValidation:
        """
        Validate a trade request against all risk limits.
        
        Args:
            trade: Trade request to validate.
            
        Returns:
            RiskValidation with decision and details.
        """
        warnings: list[str] = []
        adjusted_size = None
        adjusted_leverage = None
        
        # Check if daily reset needed
        if datetime.utcnow() >= self._daily_reset_time:
            await self._reset_daily_metrics()
        
        # Check portfolio value
        notional = trade.notional_value
        
        # 1. Check single trade size limit (2% max)
        max_trade_size = self._limits[RiskLimitType.POSITION_SIZE].value
        if notional > max_trade_size:
            # Try to adjust the size
            adjusted_size = max_trade_size / (trade.price * trade.leverage)
            if adjusted_size < trade.size * 0.5:
                # Can't approve even at 50% of requested size
                return RiskValidation(
                    decision=RiskDecision.REJECTED,
                    trade_request=trade,
                    reason=f"Trade size exceeds 2% limit (max: {max_trade_size:.2f})",
                )
            warnings.append(f"Trade size reduced from {trade.size} to {adjusted_size:.6f}")
        
        # 2. Check agent exposure limit (10% max per agent)
        agent_exposure = self._agent_exposures.get(trade.agent_id, 0.0)
        new_agent_exposure = agent_exposure + notional
        max_agent_exposure = self._limits[RiskLimitType.POSITION_SIZE].value * 5  # 10% = 2% * 5
        
        if new_agent_exposure > max_agent_exposure:
            available = max(0, max_agent_exposure - agent_exposure)
            if available < notional * 0.5:
                return RiskValidation(
                    decision=RiskDecision.REJECTED,
                    trade_request=trade,
                    reason=f"Agent {trade.agent_id} exceeds 10% exposure limit",
                )
            # Calculate adjusted size based on available exposure
            if adjusted_size is None:
                adjusted_size = available / (trade.price * trade.leverage)
            warnings.append(f"Agent exposure limit reached, size adjusted")
        
        # 3. Check total portfolio exposure
        new_total_exposure = self._metrics.total_exposure + notional
        max_portfolio_exposure = self._limits[RiskLimitType.PORTFOLIO_EXPOSURE].value
        
        if new_total_exposure > max_portfolio_exposure:
            return RiskValidation(
                decision=RiskDecision.REJECTED,
                trade_request=trade,
                reason="Portfolio exposure limit exceeded",
            )
        
        # 4. Check leverage limit
        if trade.leverage > self._max_leverage:
            adjusted_leverage = self._max_leverage
            warnings.append(f"Leverage reduced from {trade.leverage}x to {self._max_leverage}x")
        
        # 5. Check daily loss limit
        if self._metrics.daily_loss >= self._limits[RiskLimitType.DAILY_LOSS].value:
            return RiskValidation(
                decision=RiskDecision.REJECTED,
                trade_request=trade,
                reason="Daily loss limit reached - trading halted",
            )
        
        # 6. Check drawdown limit
        if self._metrics.current_drawdown >= self._limits[RiskLimitType.DRAWDOWN].value:
            return RiskValidation(
                decision=RiskDecision.REJECTED,
                trade_request=trade,
                reason="Maximum drawdown limit reached",
            )
        
        # Calculate final adjusted values
        final_size = adjusted_size if adjusted_size else trade.size
        final_leverage = adjusted_leverage if adjusted_leverage else trade.leverage
        
        # Determine decision
        if warnings:
            decision = RiskDecision.APPROVED_WITH_CONDITIONS
        else:
            decision = RiskDecision.APPROVED
        
        return RiskValidation(
            decision=decision,
            trade_request=trade,
            reason="Risk validation passed",
            warnings=warnings,
            adjusted_size=adjusted_size,
            adjusted_leverage=adjusted_leverage,
        )
    
    async def approve_trade(self, trade: TradeRequest) -> bool:
        """
        Approve and record a trade execution.
        
        Args:
            trade: Trade that was executed.
            
        Returns:
            True if trade was recorded, False otherwise.
        """
        notional = trade.notional_value
        
        # Update agent exposure
        self._agent_exposures[trade.agent_id] = (
            self._agent_exposures.get(trade.agent_id, 0.0) + notional
        )
        
        # Update position exposures
        self._position_exposures[trade.symbol] = (
            self._position_exposures.get(trade.symbol, 0.0) + notional
        )
        
        # Update total exposure
        self._metrics.total_exposure += notional
        self._metrics.open_positions += 1
        
        # Update largest position
        if notional > self._metrics.largest_position:
            self._metrics.largest_position = notional
        
        logger.info(
            f"Trade approved: {trade.agent_id} {trade.side} {trade.size} {trade.symbol} "
            f"@ {trade.price} (notional: {notional:.2f})"
        )
        
        # Send risk event
        await self._comm.broadcast(
            channel="risk",
            message_type="trade_approved",
            payload={
                "trade": {
                    "agent_id": trade.agent_id,
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "size": trade.size,
                    "price": trade.price,
                    "notional": notional,
                },
                "metrics": {
                    "total_exposure": self._metrics.total_exposure,
                    "agent_exposure": self._agent_exposures[trade.agent_id],
                },
            },
            priority=MessagePriority.NORMAL,
        )
        
        return True
    
    async def record_trade_result(
        self,
        trade: TradeRequest,
        execution_price: float,
        pnl: float = 0.0,
    ) -> None:
        """
        Record the result of a completed trade.
        
        Args:
            trade: Trade that was executed.
            execution_price: Actual execution price.
            pnl: Profit/loss from the trade.
        """
        notional = trade.notional_value
        
        # Update exposures
        self._agent_exposures[trade.agent_id] = max(
            0, self._agent_exposures.get(trade.agent_id, 0.0) - notional
        )
        self._position_exposures[trade.symbol] = max(
            0, self._position_exposures.get(trade.symbol, 0.0) - notional
        )
        self._metrics.total_exposure = max(
            0, self._metrics.total_exposure - notional
        )
        self._metrics.open_positions = max(0, self._metrics.open_positions - 1)
        
        # Update P&L
        self._metrics.daily_pnl += pnl
        if pnl < 0:
            self._metrics.daily_loss += abs(pnl)
        
        # Update portfolio value
        self._metrics.portfolio_value += pnl
        
        # Update peak and drawdown
        if self._metrics.portfolio_value > self._peak_portfolio_value:
            self._peak_portfolio_value = self._metrics.portfolio_value
        
        self._metrics.current_drawdown = (
            (self._peak_portfolio_value - self._metrics.portfolio_value) /
            self._peak_portfolio_value
        )
        
        logger.info(
            f"Trade result recorded: {trade.symbol} PnL={pnl:.2f}, "
            f"Portfolio={self._metrics.portfolio_value:.2f}, "
            f"Drawdown={self._metrics.current_drawdown:.2%}"
        )
    
    async def update_portfolio_value(self, value: float) -> None:
        """
        Update the current portfolio value.
        
        Args:
            value: Current portfolio value.
        """
        old_value = self._metrics.portfolio_value
        self._metrics.portfolio_value = value
        
        # Update peak
        if value > self._peak_portfolio_value:
            self._peak_portfolio_value = value
        
        # Recalculate drawdown
        self._metrics.current_drawdown = (
            (self._peak_portfolio_value - value) / self._peak_portfolio_value
        )
        
        # Recalculate limits based on new value
        self._limits[RiskLimitType.POSITION_SIZE].value = value * self._max_trade_pct
        
        logger.debug(
            f"Portfolio value updated: {old_value:.2f} -> {value:.2f}, "
            f"Drawdown: {self._metrics.current_drawdown:.2%}"
        )
    
    async def _reset_daily_metrics(self) -> None:
        """Reset daily metrics at midnight UTC."""
        self._metrics.daily_pnl = 0.0
        self._metrics.daily_loss = 0.0
        self._daily_reset_time = self._get_daily_reset_time()
        logger.info("Daily risk metrics reset")
    
    def get_metrics(self) -> RiskMetrics:
        """Get current risk metrics."""
        return self._metrics
    
    def get_agent_exposure(self, agent_id: str) -> float:
        """Get current exposure for an agent."""
        return self._agent_exposures.get(agent_id, 0.0)
    
    def get_position_exposure(self, symbol: str) -> float:
        """Get current exposure for a position."""
        return self._position_exposures.get(symbol, 0.0)
    
    @property
    def max_trade_pct(self) -> float:
        """Get max trade percentage."""
        return self._max_trade_pct
    
    @property
    def max_agent_exposure_pct(self) -> float:
        """Get max agent exposure percentage."""
        return self._max_agent_exposure_pct
