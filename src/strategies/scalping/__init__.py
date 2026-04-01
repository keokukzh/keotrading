"""
Scalping Strategies
==================

Mean reversion and momentum scalping strategies.
"""

from src.strategies.scalping.mean_reversion import (
    MeanReversionStrategy,
    MeanReversionConfig,
    MarketData as MRMarketData,
    StrategySignal as MRStrategySignal,
    SignalType as MRSignalType,
)
from src.strategies.scalping.momentum import (
    MomentumStrategy,
    MomentumConfig,
    MarketData as MMMarketData,
    StrategySignal as MMStrategySignal,
    SignalType as MMSignalType,
)

__all__ = [
    "MeanReversionStrategy",
    "MeanReversionConfig",
    "MomentumStrategy",
    "MomentumConfig",
]
