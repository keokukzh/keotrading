# KEOTrading Strategies

## Overview

This document describes all trading strategies implemented in the KEOTrading system.

## Table of Contents

1. [LP Arbitrage](#lp-arbitrage)
2. [Scalping - Mean Reversion](#scalping---mean-reversion)
3. [Scalping - Momentum](#scalping---momentum)
4. [Grid Trading](#grid-trading)
5. [Momentum Trend Following](#momentum-trend-following)
6. [Strategy Factory](#strategy-factory)

---

## LP Arbitrage

### Description

LP (Liquidity Provider) Arbitrage finds optimal multi-lateral arbitrage paths across exchanges and pools. Uses MILP (Mixed Integer Linear Programming) optimization via the PULP library (CBC solver) to maximize profit while respecting balance constraints.

### Key Files

- `src/strategies/arbitrage/lp_optimizer.py` - Path optimization using PULP
- `src/strategies/arbitrage/execution.py` - Multi-threaded execution engine

### Entry/Exit Conditions

**Entry (Arbitrage Path Found):**
- Optimal path exists with profit > `min_profit_pct`
- All legs have sufficient liquidity
- Balance constraints are satisfied

**Exit:**
- Target profit reached
- Timeout (30s default)
- Insufficient liquidity detected

### Position Sizing

- Capital allocation per leg based on orderbook depth
- Amount optimizer minimizes slippage
- Geometric split for large orders (multiple slices)

### Performance Expectations

- **Return:** 3-8% monthly (market dependent)
- **Risk:** Very Low
- **Speed:** Fast (sub-second to minutes)
- **Best For:** Steady small gains, low-risk farming

### Configuration

```yaml
arbitrage:
  min_spread_pct: 0.2      # Minimum profit threshold
  position_size_usd: 100   # Position size per leg
  max_path_length: 5        # Maximum arbitrage legs
  timeout_seconds: 30       # Execution timeout
```

---

## Scalping - Mean Reversion

### Description

Mean reversion scalping strategy that trades when price deviates significantly from its moving average. Uses RSI and Bollinger Bands for confirmation.

### Strategy Logic

```
Entry BUY:
  - Price < MA(20) by deviation_threshold_pct (default 1.5%)
  - RSI < 30 (oversold)
  - Optional: Price at or below lower Bollinger Band

Entry SELL:
  - Price > MA(20) by deviation_threshold_pct
  - RSI > 70 (overbought)
  - Optional: Price at or above upper Bollinger Band

Exit:
  - Price reverts to within 0.5x threshold of MA
  - Stop loss triggered
  - Take profit reached
```

### Key File

`src/strategies/scalping/mean_reversion.py`

### Indicators Used

| Indicator | Period | Purpose |
|-----------|--------|---------|
| SMA | 20 | Mean reference |
| RSI | 14 | Overbought/oversold |
| Bollinger Bands | 20 | Deviation measurement |

### Position Sizing (2% Risk Rule)

```
Risk Amount = Total Capital × 2%
Position Size = Risk Amount / Stop Loss Distance
```

### Entry/Exit Conditions

**Entry BUY:**
- Price deviates below MA(20) by >1.5%
- RSI confirms oversold (<30)
- Confidence score > 60%

**Entry SELL:**
- Price deviates above MA(20) by >1.5%
- RSI confirms overbought (>70)
- Confidence score > 60%

**Exit:**
- Price within 0.75% of MA
- Stop loss at 0.5% (configurable)
- Take profit at 0.8% (configurable)

### Performance Expectations

- **Return:** 5-15% monthly
- **Risk:** Medium
- **Speed:** Very Fast (minutes to hours)
- **Best For:** Volatile markets, ranging conditions

### Configuration

```yaml
scalping_mean_reversion:
  indicators:
    ma_period: 20
    rsi_period: 14
    bb_period: 20
    bb_std: 2
  deviation_threshold_pct: 1.5
  position_size_usd: 50
  stop_loss_pct: 0.5
  take_profit_pct: 0.8
  risk_per_trade_pct: 2.0
```

---

## Scalping - Momentum

### Description

Momentum breakout scalping strategy that trades in the direction of strong trends. Uses EMA crossover with volume confirmation and implements trailing stops.

### Strategy Logic

```
Entry BUY (Golden Cross):
  - EMA(9) crosses above EMA(21)
  - Volume spike > 1.5x average
  - Price above EMA(50) for trend confirmation (optional)

Entry SELL (Death Cross):
  - EMA(9) crosses below EMA(21)
  - Volume spike > 1.5x average
  - Price below EMA(50) for trend confirmation (optional)

Exit:
  - Trailing stop triggered
  - Opposite crossover
  - Take profit reached
```

### Key File

`src/strategies/scalping/momentum.py`

### Indicators Used

| Indicator | Period | Purpose |
|-----------|--------|---------|
| EMA | 9 | Fast trend |
| EMA | 21 | Slow trend |
| EMA | 50 | Trend confirmation |
| Volume MA | 20 | Volume baseline |

### Trailing Stop Implementation

```python
# For long positions:
trailing_stop = highest_price_since_entry × (1 - trailing_stop_pct)

# When price exceeds highest, update:
highest_price_since_entry = current_price

# Exit when price drops below trailing_stop
```

### Position Sizing (2% Risk Rule)

```
Risk Amount = Total Capital × 2%
Position Size = Risk Amount / Stop Loss Distance
Max Position = 20% of Capital
```

### Entry/Exit Conditions

**Entry BUY:**
- EMA(9) crosses above EMA(21)
- Volume > 1.5x 20-period volume MA
- (Optional) Price > EMA(50)

**Entry SELL:**
- EMA(9) crosses below EMA(21)
- Volume > 1.5x 20-period volume MA
- (Optional) Price < EMA(50)

**Exit:**
- Trailing stop: 0.3% (activates after 0.3% profit)
- Stop loss: 0.8%
- Take profit: 1.5%

### Performance Expectations

- **Return:** 8-15% monthly
- **Risk:** Medium
- **Speed:** Very Fast (minutes)
- **Best For:** Trending markets with volume

### Configuration

```yaml
scalping_momentum:
  indicators:
    ema_fast: 9
    ema_slow: 21
    volume_ma: 20
  volume_threshold: 1.5
  position_size_usd: 50
  stop_loss_pct: 0.8
  take_profit_pct: 1.5
  trailing_stop_pct: 0.3
  risk_per_trade_pct: 2.0
```

---

## Grid Trading

### Description

Grid trading bot places a series of buy and sell orders at regular price intervals (grid levels) within a configured range. Profits from price oscillations by buying low and selling high within each grid cell.

### Strategy Logic

```
1. Define price range: [lower_bound, upper_bound]
2. Create N grid levels evenly spaced in range
3. Place buy orders at each level below current price
4. When buy fills → place sell order at higher price
5. When sell fills → place new buy order at this level
6. Repeat
```

### Key File

`src/strategies/grid/grid_bot.py`

### Grid Structure

```
Upper Bound (e.g., $50,500)
  Level 10: Price $50,400 ─┬─ Sell order
  Level 9:  Price $50,300 ─┤
  Level 8:  Price $50,200 ─┤
  Level 7:  Price $50,100 ─┼─ Current price zone
  Level 6:  Price $50,000 ─┤
  Level 5:  Price $49,900 ─┼─ Buy orders
  Level 4:  Price $49,800 ─┤
  Level 3:  Price $49,700 ─┤
  Level 2:  Price $49,600 ─┤
  Level 1:  Price $49,500 ─┴─ Sell order
Lower Bound (e.g., $49,400)
```

### Profit Calculation

```
Per completed grid cycle:
  Buy at: $49,900
  Sell at: $50,000 (grid step higher)
  Profit = $50,000 - $49,900 - fees
         = $100 - ($100 × 0.2% × 2)
         = $99.60
```

### Auto-Rebalancing

When price moves outside grid bounds:
1. Detect price outside [lower, upper]
2. Recalculate bounds centered on new price
3. Reset grid levels
4. Keep track of existing positions

### Entry/Exit Conditions

**Entry (Grid Start):**
- Initialize grid with current price
- Place initial buy orders at each level

**Exit:**
- Manual stop
- All levels complete (rare)
- Price leaves grid for extended period

### Performance Expectations

- **Return:** 2-5% monthly
- **Risk:** Low
- **Speed:** Medium
- **Best For:** Ranging markets, stable volatility

### Configuration

```yaml
grid:
  pair: BTC/USDT
  grid_range_pct: 5          # 5% range from center
  grid_levels: 10            # Number of grid levels
  capital_per_level_usd: 20  # $20 per level
  total_capital_usd: 200    # Total $200
  auto_rebalance: true      # Rebalance when price exits
  maker_fee: 0.001          # 0.1%
```

---

## Momentum Trend Following

### Description

Long-term trend following strategy using EMA crossover (50/200) combined with ADX trend strength filter. Designed for 4H timeframe analysis with larger stop losses and take profits.

### Strategy Logic

```
Entry BUY:
  - EMA(50) crosses above EMA(200) (Golden Cross)
  - ADX > 25 (confirming trend strength)
  - +DI > -DI (bullish directional movement)
  - Price above both EMAs

Entry SELL:
  - EMA(50) crosses below EMA(200) (Death Cross)
  - ADX > 25 (confirming trend strength)
  - -DI > +DI (bearish directional movement)
  - Price below both EMAs

Exit:
  - Opposite crossover
  - Stop loss (3%)
  - Take profit (5-10%)
  - ADX drops < 12.5 (trend weakening)
```

### Key File

`src/strategies/momentum/trend_follower.py`

### Indicators Used

| Indicator | Period | Purpose |
|-----------|--------|---------|
| EMA | 50 | Fast trend |
| EMA | 200 | Slow trend |
| ADX | 14 | Trend strength |
| +DI | 14 | Bullish direction |
| -DI | 14 | Bearish direction |

### ADX Trend Strength

| ADX Value | Strength | Interpretation |
|-----------|----------|----------------|
| < 25 | Weak | No trend, avoid |
| 25-50 | Moderate | Valid trend |
| 50-75 | Strong | Strong trend |
| > 75 | Very Strong | Extreme trend |

### Position Sizing (2% Risk Rule)

```
Risk Amount = Total Capital × 2%
Position Size = Risk Amount / (Entry - Stop Loss)
Max Position = 30% of Capital
```

### Entry/Exit Conditions

**Entry BUY:**
- EMA(50) crosses above EMA(200)
- ADX >= 25
- +DI > -DI
- Price above EMA(50)

**Entry SELL:**
- EMA(50) crosses below EMA(200)
- ADX >= 25
- -DI > +DI
- Price below EMA(50)

**Exit:**
- Opposite crossover
- Stop loss: 3%
- Take profit: 8% (default, adjustable 5-10%)
- ADX < 12.5 (trend exhaustion)

### Performance Expectations

- **Return:** 10-30% monthly
- **Risk:** Medium-High
- **Speed:** Slow (4H+ candles)
- **Best For:** Trending markets, swing trading

### Configuration

```yaml
momentum:
  pair: BTC/USDT
  timeframe: 4h
  indicators:
    ema_fast: 50
    ema_slow: 200
    adx_period: 14
  adx_threshold: 25
  position_size_usd: 100
  stop_loss_pct: 3.0
  take_profit_pct: 8.0
  risk_per_trade_pct: 2.0
```

---

## Strategy Factory

### Description

Factory pattern for creating and managing strategy instances. Provides a registry of all available strategies with parameter validation.

### Key File

`src/strategies/factory.py`

### Available Strategies

| Strategy Name | Class | Description |
|---------------|-------|-------------|
| `mean_reversion` | MeanReversionStrategy | MA/RSI/BB mean reversion scalping |
| `momentum` | MomentumStrategy | EMA crossover momentum scalping |
| `grid` | GridBot | Grid trading bot |
| `trend_follower` | TrendFollowerStrategy | EMA(50/200) + ADX trend following |
| `arbitrage` | ArbitragePathOptimizer | LP arbitrage path optimization |

### Usage

```python
from src.strategies.factory import StrategyFactory

# Initialize factory
factory = StrategyFactory(config={"risk_per_trade_pct": 2.0})

# Create strategy
strategy = factory.create(
    "mean_reversion",
    pair="BTC/USDT",
    exchange="binance",
    config={"ma_period": 20, "rsi_period": 14}
)

# Validate config
is_valid, error = factory.validate_config("mean_reversion", config)

# Get signal
signal = strategy.get_signal(market_data)

# List available strategies
strategies = factory.list_strategies()
```

### Validation

All strategies validate configuration on creation:

```python
# MeanReversionStrategy validates:
- MA period >= 2
- RSI period >= 2
- Deviation threshold > 0
- Risk per trade 0-100%
- Stop loss and take profit > 0

# MomentumStrategy validates:
- EMA fast < EMA slow
- EMA fast >= 2
- Volume threshold > 0
- Trailing stop > 0

# GridBot validates:
- Grid levels >= 2
- Grid range > 0
- Capital per level > 0
- Total capital sufficient for grid

# TrendFollowerStrategy validates:
- EMA fast < EMA slow
- ADX threshold > 0
- ADX period >= 1
- Stop loss and take profit > 0
```

---

## Common Configuration Parameters

### Position Sizing (2% Risk Rule)

All strategies use the 2% risk rule for position sizing:

```
Risk Amount = Total Capital × Risk %
Position Size = Risk Amount / Stop Loss %

Example:
  Capital = $10,000
  Risk % = 2%
  Risk Amount = $200
  Stop Loss = 2%
  Position Size = $200 / 2% = $10,000 / Entry Price
```

### Risk Management

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| `risk_per_trade_pct` | Max risk per trade | 2% |
| `max_position_pct` | Max position size | 20-30% |
| `stop_loss_pct` | Stop loss percentage | 0.5-5% |
| `take_profit_pct` | Take profit percentage | 0.8-10% |

---

## Performance Summary

| Strategy | Return | Risk | Speed | Best Market |
|----------|--------|------|-------|-------------|
| **LP Arbitrage** | 3-8% | Very Low | Fast | All (spread dependent) |
| **Mean Reversion** | 5-15% | Medium | Very Fast | Ranging/Volatile |
| **Momentum** | 8-15% | Medium | Very Fast | Trending |
| **Grid** | 2-5% | Low | Medium | Ranging |
| **Trend Following** | 10-30% | Medium-High | Slow | Strong Trends |

---

## Implementation Notes

- All strategies use Python 3.11+ syntax
- Type hints on all functions
- Docstrings for classes and methods
- Logging on all entry/exit points
- No hardcoded values - all from config
- Signals include confidence scores (0-1)
- Position sizing follows 2% risk rule
