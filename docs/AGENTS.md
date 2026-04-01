# Agents Specification

## Overview

50 agents organized in 4 layers, each with specific responsibilities.

---

## Layer 1: Data Agents (10)

### Price Monitors (4)
```
Agent IDs: data_price_01, data_price_02, data_price_03, data_price_04
Exchanges: Binance, Kraken, Coinbase, Bybit
Data: Real-time price via WebSocket
Output Channel: {pair}:price
Update Frequency: < 100ms
```

### Orderbook Analyzers (2)
```
Agent IDs: data_ob_01, data_ob_02
Data: Orderbook depth, spread, liquidity
Output Channel: {pair}:orderbook
Analysis: Spread %, depth imbalance, whale detection
```

### News/Sentiment Trackers (2)
```
Agent IDs: data_news_01, data_news_02
Sources: Twitter/X, Reddit, CoinGecko, CryptoPanic
Output Channel: market:sentiment
Scoring: -1.0 (bearish) to +1.0 (bullish)
```

### Volume Analyzers (2)
```
Agent IDs: data_vol_01, data_vol_02
Data: 24h volume, volume spikes, unusual activity
Output Channel: {pair}:volume
Alerts: Volume > 2x average
```

---

## Layer 2: Strategy Agents (25)

### Arbitrage Agents (8)

#### Cross-Exchange Arbitrage (3)
```
Agent IDs: strat_arb_cex_01, strat_arb_cex_02, strat_arb_cex_03
Logic: Buy on Exchange A, sell on Exchange B when price diff > fees
Min Spread: 0.5% (after fees)
Position Size: $10-50 per trade
Execution: CEX Executor
```

#### DEX Arbitrage (3)
```
Agent IDs: strat_arb_dex_01, strat_arb_dex_02, strat_arb_dex_03
Logic: Triangle arbitrage on Solana DEXs
Pools: SOL-USDC, SOL-USDT, BTC-SOL, ETH-SOL
Min Spread: 0.2% (after fees)
Position Size: $20-100 per trade
Execution: DEX Executor
```

#### Triangle Arbitrage (2)
```
Agent IDs: strat_triangle_01, strat_triangle_02
Logic: BTC→ETH→USDT→BTC or similar cycles
Min Spread: 0.3%
Execution: CEX Executor
```

### Scalping Agents (8)

#### Mean Reversion Scalpers (4)
```
Agent IDs: strat_scalp_mr_01, strat_scalp_mr_02, strat_scalp_mr_03, strat_scalp_mr_04
Logic: Price deviates from 20-period MA → expect reversion
Indicators: MA(20), RSI(14), Bollinger Bands
Position Size: $20-100
Stop Loss: 0.5%
Take Profit: 0.3-0.8%
```

#### Momentum Scalpers (4)
```
Agent IDs: strat_scalp_mom_01, strat_scalp_mom_02, strat_scalp_mom_03, strat_scalp_mom_04
Logic: Breakout followed by momentum continuation
Indicators: EMA(9), EMA(21), Volume spike
Position Size: $20-100
Stop Loss: 0.8%
Take Profit: 0.5-1.5%
```

### Grid Agents (5)
```
Agent IDs: strat_grid_01, strat_grid_02, strat_grid_03, strat_grid_04, strat_grid_05
Pairs: BTC, ETH, SOL, AVAX, LINK
Grid Levels: 10 levels equidistant
Grid Range: 5-10% of current price
Position Size: $10-20 per grid level
Rebalance: When filled, reset grid
```

### Momentum Agents (4)
```
Agent IDs: strat_momentum_01, strat_momentum_02, strat_momentum_03, strat_momentum_04
Logic: Trend continuation on 4H timeframe
Indicators: EMA(50), EMA(200), ADX
Position Size: $50-200
Stop Loss: 3%
Take Profit: 5-10%
Holding Period: Hours to days
```

---

## Layer 3: Execution Agents (10)

### CEX Executors (4)
```
Agent IDs: exec_cex_01, exec_cex_02, exec_cex_03, exec_cex_04
Exchanges: Binance, Kraken, Coinbase, Bybit
Order Types: Market, Limit (post-only)
Retry: 3 attempts on failure
Slippage Tolerance: 0.5%
```

### DEX Executors (4)
```
Agent IDs: exec_dex_01, exec_dex_02, exec_dex_03, exec_dex_04
DEXs: Raydium, Orca, Marinade, Jupiter
Priority: Lowest gas, best execution
Retry: 3 attempts
Timeout: 30 seconds
```

### Flash Loan Coordinators (2)
```
Agent IDs: exec_flash_01, exec_flash_02
Protocol: Solend, Jet Protocol
Max Loan: $1000 equivalent
Purpose: Leverage without capital
```

---

## Layer 4: Risk & Portfolio (5)

### Risk Managers (2)
```
Agent IDs: risk_mgmt_01, risk_mgmt_02
Rules:
  - Max 2% position size
  - Max 10% per agent
  - Daily drawdown > 5% → pause all
  - Weekly loss > 8% → reduce position 50%
Actions: Auto-pause agents, hard stops
```

### Portfolio Rebalancer (1)
```
Agent ID: risk_rebalancer_01
Schedule: Every 4 hours
Logic: Maintain target allocation
Threshold: 5% deviation triggers rebalance
```

### P&L Tracker (1)
```
Agent ID: risk_pnl_01
Metrics: Realized P&L, unrealized P&L, win rate
Reporting: Per agent, per strategy, total
```

### Compliance Monitor (1)
```
Agent ID: risk_compliance_01
Rules: No wash trading, no insider trading signals
Logging: Full audit trail
Alerts: Suspicious patterns
```

---

## Agent Communication

### Subscribe Channels
```
Data Agents publish to: {pair}:{data_type}
Strategy Agents subscribe to: {relevant_pairs}:price, orderbook
Strategy Agents publish to: agent:orchestrator:signals
Execution Agents subscribe to: agent:orchestrator:execution
Risk Agents subscribe to: agent:orchestrator:trades, system:alerts
```

### Message Format
```json
{
  "agent_id": "strat_arb_cex_01",
  "type": "SIGNAL",
  "payload": {
    "action": "BUY",
    "pair": "BTC/USDT",
    "amount": 0.01,
    "exchange": "binance",
    "reason": "arb_cross_exchange",
    "expected_profit": 0.004,
    "urgency": "HIGH"
  },
  "timestamp": 1711929600000
}
```

---

## Agent Lifecycle

### States
- `INIT` - Initializing
- `SUBSCRIBING` - Connecting to data sources
- `RUNNING` - Active and trading
- `PAUSED` - Temporarily stopped (risk event)
- `ERROR` - Exception occurred, needs review
- `STOPPED` - Shut down

### State Transitions
```
INIT → SUBSCRIBING → RUNNING
RUNNING → PAUSED (risk/drawdown)
PAUSED → RUNNING (manual/risk cleared)
RUNNING → ERROR (exception)
ERROR → RUNNING (after review)
ANY → STOPPED (shutdown)
```
