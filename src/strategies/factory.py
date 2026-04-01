"""
Strategy Factory
================

Factory pattern for creating and managing trading strategy instances.
Provides registry of all available strategies and parameter validation.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Type, Dict, Callable, Any

from src.strategies.scalping.mean_reversion import (
    MeanReversionStrategy,
    MeanReversionConfig,
    MarketData as MRMarketData,
    SignalType as MRSignalType,
)
from src.strategies.scalping.momentum import (
    MomentumStrategy,
    MomentumConfig,
    MarketData as MMMarketData,
    SignalType as MMSignalType,
)
from src.strategies.grid.grid_bot import (
    GridBot,
    GridConfig,
)
from src.strategies.momentum.trend_follower import (
    TrendFollowerStrategy,
    TrendFollowerConfig,
    MarketData as TFMarketData,
    SignalType as TFSignalType,
)
from src.strategies.arbitrage.lp_optimizer import (
    ArbitragePathOptimizer,
    AmountOptimizer,
    PoolInfo,
    BalanceInfo,
)
from src.strategies.arbitrage.execution import (
    ArbitrageExecutionEngine,
)

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Available strategy types."""
    ARBITRAGE = "arbitrage"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM_SCALPING = "momentum_scalping"
    GRID = "grid"
    TREND_FOLLOWER = "trend_follower"


class StrategyFactory:
    """
    Factory for creating and managing strategy instances.
    
    Usage:
        factory = StrategyFactory()
        
        # Create a strategy
        strategy = factory.create("mean_reversion", pair="BTC/USDT")
        
        # Get signal
        signal = strategy.get_signal(market_data)
        
        # Validate config
        is_valid, error = factory.validate_config("mean_reversion", config)
    """
    
    # Registry of strategy constructors
    _registry: Dict[str, Callable] = {}
    _config_validators: Dict[str, Callable] = {}
    
    @classmethod
    def register(cls, strategy_name: str):
        """
        Decorator to register a strategy.
        
        Usage:
            @StrategyFactory.register("my_strategy")
            def create_my_strategy(config):
                return MyStrategy(config)
        """
        def decorator(func: Callable):
            cls._registry[strategy_name] = func
            return func
        return decorator
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize strategy factory.
        
        Args:
            config: Optional global configuration dict
        """
        self.config = config or {}
        self._instances: Dict[str, Any] = {}
        
        # Register default strategies
        self._register_default_strategies()
        
        logger.info(f"Initialized StrategyFactory with {len(self._registry)} strategies")
    
    def _register_default_strategies(self):
        """Register all default strategies."""
        # These are registered via the decorator on each strategy class
        pass
    
    def create(
        self,
        strategy_name: str,
        pair: str = "BTC/USDT",
        exchange: str = "binance",
        config: Optional[dict] = None,
        **kwargs,
    ) -> Any:
        """
        Create a strategy instance by name.
        
        Args:
            strategy_name: Name of strategy to create
            pair: Trading pair
            exchange: Exchange name
            config: Optional strategy-specific config dict
            **kwargs: Additional arguments
            
        Returns:
            Strategy instance
            
        Raises:
            ValueError: If strategy name is unknown
        """
        logger.info(f"Creating strategy: {strategy_name} for {pair} on {exchange}")
        
        # Merge configs
        merged_config = {**self.config, **(config or {})}
        
        # Create based on strategy type
        strategy_name_lower = strategy_name.lower()
        
        if strategy_name_lower in ["mean_reversion", "scalping_mean_reversion"]:
            return self._create_mean_reversion(pair, exchange, merged_config, **kwargs)
        
        elif strategy_name_lower in ["momentum", "scalping_momentum", "momentum_scalping"]:
            return self._create_momentum(pair, exchange, merged_config, **kwargs)
        
        elif strategy_name_lower in ["grid", "grid_trading"]:
            return self._create_grid(pair, exchange, merged_config, **kwargs)
        
        elif strategy_name_lower in ["trend_follower", "momentum_trend", "trend"]:
            return self._create_trend_follower(pair, exchange, merged_config, **kwargs)
        
        elif strategy_name_lower in ["arbitrage", "lp_arbitrage", "lp"]:
            return self._create_arbitrage(merged_config, **kwargs)
        
        else:
            raise ValueError(
                f"Unknown strategy: {strategy_name}. "
                f"Available: {list(self._registry.keys())}"
            )
    
    def _create_mean_reversion(
        self,
        pair: str,
        exchange: str,
        config: dict,
        **kwargs,
    ) -> MeanReversionStrategy:
        """Create mean reversion strategy."""
        strategy_config = MeanReversionConfig(
            ma_period=config.get("ma_period", 20),
            rsi_period=config.get("rsi_period", 14),
            bb_period=config.get("bb_period", 20),
            bb_std=config.get("bb_std", 2.0),
            deviation_threshold_pct=config.get("deviation_threshold_pct", 1.5),
            rsi_oversold=config.get("rsi_oversold", 30.0),
            rsi_overbought=config.get("rsi_overbought", 70.0),
            stop_loss_pct=config.get("stop_loss_pct", 0.5),
            take_profit_pct=config.get("take_profit_pct", 0.8),
            risk_per_trade_pct=config.get("risk_per_trade_pct", 2.0),
            max_position_pct=config.get("max_position_pct", 20.0),
        )
        
        strategy = MeanReversionStrategy(
            config=strategy_config,
            pair=pair,
            exchange=exchange,
        )
        
        self._instances[f"{pair}_{exchange}_mean_reversion"] = strategy
        return strategy
    
    def _create_momentum(
        self,
        pair: str,
        exchange: str,
        config: dict,
        **kwargs,
    ) -> MomentumStrategy:
        """Create momentum scalping strategy."""
        strategy_config = MomentumConfig(
            ema_fast=config.get("ema_fast", 9),
            ema_slow=config.get("ema_slow", 21),
            ema_trend=config.get("ema_trend", 50),
            volume_ma_period=config.get("volume_ma_period", 20),
            volume_threshold=config.get("volume_threshold", 1.5),
            stop_loss_pct=config.get("stop_loss_pct", 0.8),
            take_profit_pct=config.get("take_profit_pct", 1.5),
            trailing_stop_pct=config.get("trailing_stop_pct", 0.3),
            risk_per_trade_pct=config.get("risk_per_trade_pct", 2.0),
            max_position_pct=config.get("max_position_pct", 20.0),
        )
        
        strategy = MomentumStrategy(
            config=strategy_config,
            pair=pair,
            exchange=exchange,
        )
        
        self._instances[f"{pair}_{exchange}_momentum"] = strategy
        return strategy
    
    def _create_grid(
        self,
        pair: str,
        exchange: str,
        config: dict,
        **kwargs,
    ) -> GridBot:
        """Create grid trading bot."""
        strategy_config = GridConfig(
            grid_levels=config.get("grid_levels", 10),
            grid_range_pct=config.get("grid_range_pct", 5.0),
            grid_range_top_pct=config.get("grid_range_top_pct", 5.0),
            grid_range_bottom_pct=config.get("grid_range_bottom_pct", 5.0),
            capital_per_level_usd=config.get("capital_per_level_usd", 20.0),
            total_capital_usd=config.get("total_capital_usd", 200.0),
            auto_rebalance=config.get("auto_rebalance", True),
            maker_fee=config.get("maker_fee", 0.001),
            taker_fee=config.get("taker_fee", 0.001),
        )
        
        strategy = GridBot(
            config=strategy_config,
            pair=pair,
            exchange=exchange,
        )
        
        self._instances[f"{pair}_{exchange}_grid"] = strategy
        return strategy
    
    def _create_trend_follower(
        self,
        pair: str,
        exchange: str,
        config: dict,
        **kwargs,
    ) -> TrendFollowerStrategy:
        """Create trend following strategy."""
        strategy_config = TrendFollowerConfig(
            ema_fast=config.get("ema_fast", 50),
            ema_slow=config.get("ema_slow", 200),
            adx_period=config.get("adx_period", 14),
            adx_threshold=config.get("adx_threshold", 25.0),
            timeframe=config.get("timeframe", "4h"),
            stop_loss_pct=config.get("stop_loss_pct", 3.0),
            take_profit_pct=config.get("take_profit_pct", 8.0),
            risk_per_trade_pct=config.get("risk_per_trade_pct", 2.0),
            max_position_pct=config.get("max_position_pct", 30.0),
        )
        
        strategy = TrendFollowerStrategy(
            config=strategy_config,
            pair=pair,
            exchange=exchange,
        )
        
        self._instances[f"{pair}_{exchange}_trend_follower"] = strategy
        return strategy
    
    def _create_arbitrage(
        self,
        config: dict,
        **kwargs,
    ) -> ArbitragePathOptimizer:
        """Create LP arbitrage optimizer."""
        pools = config.get("pools", [])
        balances = config.get("balances", {})
        
        pool_infos = []
        for pool in pools:
            pool_infos.append(PoolInfo(
                pool_id=pool["pool_id"],
                exchange=pool["exchange"],
                base_asset=pool["base_asset"],
                quote_asset=pool["quote_asset"],
                bid_price=pool["bid_price"],
                ask_price=pool["ask_price"],
                bid_volume=pool["bid_volume"],
                ask_volume=pool["ask_volume"],
            ))
        
        balance_infos = {
            asset: BalanceInfo(
                asset=asset,
                available=bal.get("available", 0.0),
                locked=bal.get("locked", 0.0),
            )
            for asset, bal in balances.items()
        }
        
        optimizer = ArbitragePathOptimizer(
            pools=pool_infos,
            balances=balance_infos,
            initial_capital_usd=config.get("initial_capital_usd", 1000.0),
            min_profit_pct=config.get("min_profit_pct", 0.1),
            max_path_length=config.get("max_path_length", 5),
        )
        
        self._instances["arbitrage_optimizer"] = optimizer
        return optimizer
    
    def get_instance(self, key: str) -> Optional[Any]:
        """Get an existing strategy instance by key."""
        return self._instances.get(key)
    
    def list_strategies(self) -> list[str]:
        """List all registered strategy names."""
        return [
            "mean_reversion",
            "momentum",
            "grid",
            "trend_follower",
            "arbitrage",
        ]
    
    def validate_config(
        self,
        strategy_name: str,
        config: dict,
    ) -> tuple[bool, str]:
        """
        Validate strategy configuration.
        
        Args:
            strategy_name: Name of strategy
            config: Configuration dict to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        strategy_name_lower = strategy_name.lower()
        
        if strategy_name_lower in ["mean_reversion", "scalping_mean_reversion"]:
            try:
                strategy_config = MeanReversionConfig(**config)
                strategy = MeanReversionStrategy(config=strategy_config)
                return strategy.validate_config()
            except Exception as e:
                return False, str(e)
        
        elif strategy_name_lower in ["momentum", "scalping_momentum", "momentum_scalping"]:
            try:
                strategy_config = MomentumConfig(**config)
                strategy = MomentumStrategy(config=strategy_config)
                return strategy.validate_config()
            except Exception as e:
                return False, str(e)
        
        elif strategy_name_lower in ["grid", "grid_trading"]:
            try:
                strategy_config = GridConfig(**config)
                strategy = GridBot(config=strategy_config)
                return strategy.validate_config()
            except Exception as e:
                return False, str(e)
        
        elif strategy_name_lower in ["trend_follower", "momentum_trend", "trend"]:
            try:
                strategy_config = TrendFollowerConfig(**config)
                strategy = TrendFollowerStrategy(config=strategy_config)
                return strategy.validate_config()
            except Exception as e:
                return False, str(e)
        
        elif strategy_name_lower in ["arbitrage", "lp_arbitrage", "lp"]:
            # Basic validation for arbitrage config
            if "pools" not in config:
                return False, "pools list required"
            if "balances" not in config:
                return False, "balances dict required"
            return True, "Valid"
        
        else:
            return False, f"Unknown strategy: {strategy_name}"


# Import Enum for StrategyType
from enum import Enum
