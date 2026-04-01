"""
Momentum/Trend Following Strategies
==================================
"""

from src.strategies.momentum.trend_follower import (
    TrendFollowerStrategy,
    TrendFollowerConfig,
    MarketData as TFMarketData,
    StrategySignal as TFStrategySignal,
    SignalType as TFSignalType,
    TrendStrength,
)

__all__ = [
    "TrendFollowerStrategy",
    "TrendFollowerConfig",
    "TrendStrength",
]
