"""
Backtesting Engine
Strategy validation and performance testing on historical data.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class BacktestMode(Enum):
    """Backtest mode."""
    STANDARD = "standard"
    WALK_FORWARD = "walk_forward"
    MONTE_CARLO = "monte_carlo"


@dataclass
class BacktestConfig:
    """Configuration for a backtest."""
    name: str
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    fee_rate: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%
    mode: BacktestMode = BacktestMode.STANDARD


@dataclass
class BacktestTrade:
    """Represents a trade in backtest."""
    entry_time: datetime
    exit_time: datetime
    side: str  # "long" or "short"
    entry_price: float
    exit_price: float
    amount: float
    pnl: float
    pnl_pct: float
    commission: float
    slippage_cost: float


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    config: BacktestConfig
    trades: List[BacktestTrade]
    equity_curve: pd.DataFrame
    
    # Summary metrics
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_trade: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_holding_period: timedelta
    
    # Monthly returns
    monthly_returns: Dict[str, float]


class MarketDataSource:
    """Source of market data for backtesting."""
    
    async def fetch_ohlcv(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime,
        timeframe: str = "1h"
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for backtesting.
        Returns DataFrame with columns: timestamp, open, high, low, close, volume
        """
        raise NotImplementedError


class CSVDataSource(MarketDataSource):
    """Load market data from CSV files."""
    
    def __init__(self, data_dir: str = "data/market_data"):
        self.data_dir = data_dir
    
    async def fetch_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str = "1h"
    ) -> pd.DataFrame:
        """Load from CSV file."""
        import os
        
        # Map symbol to filename
        filename = f"{symbol.replace('/', '_')}_{timeframe}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            # Generate mock data for demo
            return self._generate_mock_data(symbol, start, end, timeframe)
        
        df = pd.read_csv(filepath, parse_dates=['timestamp'])
        df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
        return df
    
    def _generate_mock_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str
    ) -> pd.DataFrame:
        """Generate realistic mock OHLCV data."""
        # Determine frequency
        if timeframe == "1m":
            freq = timedelta(minutes=1)
            periods = int((end - start).total_seconds() / 60)
        elif timeframe == "5m":
            freq = timedelta(minutes=5)
            periods = int((end - start).total_seconds() / 300)
        elif timeframe == "1h":
            freq = timedelta(hours=1)
            periods = int((end - start).total_seconds() / 3600)
        elif timeframe == "4h":
            freq = timedelta(hours=4)
            periods = int((end - start).total_seconds() / 14400)
        else:  # 1d
            freq = timedelta(days=1)
            periods = int((end - start).total_seconds() / 86400)
        
        # Generate timestamps
        timestamps = [start + i * freq for i in range(periods)]
        
        # Base price (mock)
        if "BTC" in symbol:
            base_price = 64000
            volatility = 0.02
        elif "ETH" in symbol:
            base_price = 3400
            volatility = 0.025
        elif "SOL" in symbol:
            base_price = 150
            volatility = 0.035
        else:
            base_price = 100
            volatility = 0.03
        
        # Generate price series with random walk
        np.random.seed(42)
        returns = np.random.normal(0.0001, volatility, periods)
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLC
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            high_mult = 1 + abs(np.random.normal(0, volatility / 2))
            low_mult = 1 - abs(np.random.normal(0, volatility / 2))
            
            high = close * high_mult
            low = close * low_mult
            open_price = close * (1 + np.random.normal(0, volatility / 4))
            volume = np.random.uniform(100, 1000) * (1 + abs(np.random.normal(0, 1)))
            
            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data)


class Backtester:
    """
    Backtesting engine for strategy validation.
    """
    
    def __init__(
        self,
        data_source: Optional[MarketDataSource] = None,
        config: Optional[BacktestConfig] = None
    ):
        self.data_source = data_source or CSVDataSource()
        self.config = config
        self.strategy = None
        self.results: Optional[BacktestResult] = None
    
    async def run(
        self,
        config: BacktestConfig,
        strategy_logic: Callable[[pd.DataFrame, Dict], Dict]
    ) -> BacktestResult:
        """
        Run backtest with given configuration and strategy logic.
        
        strategy_logic: Function that takes (data, position) and returns:
            {
                'action': 'buy' | 'sell' | 'hold',
                'stop_loss': float,
                'take_profit': float,
                'position_size': float
            }
        """
        self.config = config
        
        # Fetch data
        data = await self.data_source.fetch_ohlcv(
            symbol=config.symbol,
            start=config.start_date,
            end=config.end_date,
            timeframe="1h"  # Default to 1h candles
        )
        
        if len(data) == 0:
            raise ValueError(f"No data available for {config.symbol}")
        
        # Run backtest
        trades = []
        position = None
        equity = []
        current_capital = config.initial_capital
        
        for i, row in data.iterrows():
            timestamp = row['timestamp']
            price = row['close']
            
            # Calculate current equity
            if position:
                if position['side'] == 'long':
                    unrealized_pnl = (price - position['entry_price']) * position['amount']
                else:
                    unrealized_pnl = (position['entry_price'] - price) * position['amount']
            else:
                unrealized_pnl = 0
            
            equity.append({
                'timestamp': timestamp,
                'equity': current_capital + unrealized_pnl,
                'price': price
            })
            
            # Check if we should exit position
            if position:
                should_exit = False
                
                # Stop loss hit
                if position['side'] == 'long' and price <= position['stop_loss']:
                    should_exit = True
                elif position['side'] == 'short' and price >= position['stop_loss']:
                    should_exit = True
                
                # Take profit hit
                if position['side'] == 'long' and price >= position['take_profit']:
                    should_exit = True
                elif position['side'] == 'short' and price <= position['take_profit']:
                    should_exit = True
                
                if should_exit:
                    # Close position
                    exit_price = price * (1 - config.slippage if position['side'] == 'long' else 1 + config.slippage)
                    pnl = (exit_price - position['entry_price']) * position['amount'] if position['side'] == 'long' else (position['entry_price'] - exit_price) * position['amount']
                    commission = position['entry_price'] * position['amount'] * config.fee_rate + exit_price * position['amount'] * config.fee_rate
                    slippage_cost = abs(price - exit_price) * position['amount']
                    
                    trade = BacktestTrade(
                        entry_time=position['entry_time'],
                        exit_time=timestamp,
                        side=position['side'],
                        entry_price=position['entry_price'],
                        exit_price=exit_price,
                        amount=position['amount'],
                        pnl=pnl - commission - slippage_cost,
                        pnl_pct=(pnl - commission - slippage_cost) / (position['entry_price'] * position['amount']) * 100,
                        commission=commission,
                        slippage_cost=slippage_cost
                    )
                    trades.append(trade)
                    current_capital += trade.pnl
                    position = None
            
            # Check for new signals
            if not position:
                signal = strategy_logic(data.iloc[:i+1], position)
                
                if signal and signal.get('action') == 'buy':
                    position_size = signal.get('position_size', 0.1) * current_capital
                    amount = position_size / price
                    
                    position = {
                        'side': 'long',
                        'entry_time': timestamp,
                        'entry_price': price * (1 + config.slippage),
                        'amount': amount,
                        'stop_loss': signal.get('stop_loss', price * 0.95),
                        'take_profit': signal.get('take_profit', price * 1.10)
                    }
                elif signal and signal.get('action') == 'sell':
                    position_size = signal.get('position_size', 0.1) * current_capital
                    amount = position_size / price
                    
                    position = {
                        'side': 'short',
                        'entry_time': timestamp,
                        'entry_price': price * (1 - config.slippage),
                        'amount': amount,
                        'stop_loss': signal.get('stop_loss', price * 1.05),
                        'take_profit': signal.get('take_profit', price * 0.90)
                    }
        
        # Close any open position at the end
        if position:
            last_price = data.iloc[-1]['close']
            exit_price = last_price * (1 - config.slippage if position['side'] == 'long' else 1 + config.slippage)
            pnl = (exit_price - position['entry_price']) * position['amount'] if position['side'] == 'long' else (position['entry_price'] - exit_price) * position['amount']
            
            trade = BacktestTrade(
                entry_time=position['entry_time'],
                exit_time=data.iloc[-1]['timestamp'],
                side=position['side'],
                entry_price=position['entry_price'],
                exit_price=exit_price,
                amount=position['amount'],
                pnl=pnl,
                pnl_pct=pnl / (position['entry_price'] * position['amount']) * 100,
                commission=0,
                slippage_cost=0
            )
            trades.append(trade)
            current_capital += trade.pnl
        
        # Calculate metrics
        result = self._calculate_metrics(config, trades, equity)
        self.results = result
        return result
    
    def _calculate_metrics(
        self,
        config: BacktestConfig,
        trades: List[BacktestTrade],
        equity: List[Dict]
    ) -> BacktestResult:
        """Calculate backtest performance metrics."""
        
        equity_df = pd.DataFrame(equity)
        
        # Basic metrics
        total_return = equity_df['equity'].iloc[-1] - config.initial_capital
        total_return_pct = (total_return / config.initial_capital) * 100
        
        # Calculate drawdown
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
        max_drawdown = equity_df['drawdown'].min()
        max_drawdown_pct = abs(max_drawdown)
        
        # Trade metrics
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        avg_win = total_wins / len(winning_trades) if winning_trades else 0
        avg_loss = total_losses / len(losing_trades) if losing_trades else 0
        avg_trade = sum(t.pnl for t in trades) / len(trades) if trades else 0
        
        # Holding period
        holding_periods = [t.exit_time - t.entry_time for t in trades]
        avg_holding_period = sum(holding_periods, timedelta()) / len(holding_periods) if holding_periods else timedelta()
        
        # Sharpe ratio (simplified)
        if len(trades) > 1:
            returns = [t.pnl_pct for t in trades]
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Monthly returns
        equity_df['month'] = equity_df['timestamp'].dt.to_period('M')
        monthly_returns = {}
        for month, group in equity_df.groupby('month'):
            monthly_pnl = group['equity'].iloc[-1] - group['equity'].iloc[0]
            monthly_returns[str(month)] = monthly_pnl
        
        return BacktestResult(
            config=config,
            trades=trades,
            equity_curve=equity_df,
            total_return=total_return,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade=avg_trade,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_holding_period=avg_holding_period,
            monthly_returns=monthly_returns
        )
    
    def compare_strategies(
        self,
        strategies: List[Dict],
        symbols: List[str],
        start: datetime,
        end: datetime,
        initial_capital: float = 10000
    ) -> pd.DataFrame:
        """Compare multiple strategies across symbols."""
        results = []
        
        for strategy in strategies:
            for symbol in symbols:
                config = BacktestConfig(
                    name=f"{strategy['name']}_{symbol}",
                    strategy_name=strategy['name'],
                    symbol=symbol,
                    start_date=start,
                    end_date=end,
                    initial_capital=initial_capital
                )
                
                # Run backtest
                try:
                    result = asyncio.run(self.run(config, strategy['logic']))
                    
                    results.append({
                        'Strategy': strategy['name'],
                        'Symbol': symbol,
                        'Total Return': f"${result.total_return:,.2f}",
                        'Return %': f"{result.total_return_pct:.2f}%",
                        'Sharpe': f"{result.sharpe_ratio:.2f}",
                        'Max DD': f"{result.max_drawdown_pct:.2f}%",
                        'Win Rate': f"{result.win_rate:.1f}%",
                        'Trades': result.total_trades
                    })
                except Exception as e:
                    logger.error(f"Backtest failed for {strategy['name']} on {symbol}: {e}")
        
        return pd.DataFrame(results)


def example_mean_reversion_strategy(data: pd.DataFrame, position: Dict) -> Dict:
    """Example mean reversion strategy for backtesting."""
    if len(data) < 20:
        return None
    
    # Calculate simple moving average
    sma_20 = data['close'].tail(20).mean()
    current_price = data['close'].iloc[-1]
    
    # RSI calculation
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    if position is None:
        # Entry conditions
        if current_price < sma_20 * 0.98 and current_rsi < 30:
            return {
                'action': 'buy',
                'stop_loss': current_price * 0.95,
                'take_profit': current_price * 1.05,
                'position_size': 0.1
            }
    else:
        # Exit conditions
        if current_price > sma_20 * 1.02 or current_rsi > 70:
            return {'action': 'sell'}
    
    return None


def example_momentum_strategy(data: pd.DataFrame, position: Dict) -> Dict:
    """Example momentum strategy for backtesting."""
    if len(data) < 50:
        return None
    
    # EMA crossover
    ema_12 = data['close'].ewm(span=12).mean().iloc[-1]
    ema_26 = data['close'].ewm(span=26).mean().iloc[-1]
    prev_ema_12 = data['close'].ewm(span=12).mean().iloc[-2]
    prev_ema_26 = data['close'].ewm(span=26).mean().iloc[-2]
    
    if position is None:
        # Golden cross - EMA12 crosses above EMA26
        if prev_ema_12 <= prev_ema_26 and ema_12 > ema_26:
            return {
                'action': 'buy',
                'stop_loss': data['close'].iloc[-1] * 0.97,
                'take_profit': data['close'].iloc[-1] * 1.08,
                'position_size': 0.1
            }
    else:
        # Death cross - EMA12 crosses below EMA26
        if prev_ema_12 >= prev_ema_26 and ema_12 < ema_26:
            return {'action': 'sell'}
    
    return None
