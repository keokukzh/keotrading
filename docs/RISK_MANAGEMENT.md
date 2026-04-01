# Risk Management

## Overview

KEOTrading implements a multi-layered risk management system to protect capital while maximizing growth. Risk rules are **non-negotiable** and enforced at multiple levels.

---

## Core Rules

### Position Limits

| Rule | Limit | Rationale |
|------|-------|-----------|
| Per Trade | 2% of portfolio | Max loss per trade |
| Per Agent | 10% of portfolio | Diversification |
| Per Strategy | 30% of portfolio | Strategy correlation |
| Total Leverage | 3x max | Volatility buffer |

### Stop Losses

| Strategy | Stop Loss | Notes |
|----------|-----------|-------|
| Scalping | 0.5-0.8% | Tight, frequent exits |
| Arbitrage | N/A | Pre-defined exits |
| Grid | -5% from entry | Wide, market dependent |
| Momentum | 3% | Allow room for noise |

### Drawdown Limits

| Level | Drawdown | Action |
|-------|----------|--------|
| Warning | 3% | Alert only |
| Critical | 5% | Pause aggressive agents |
| Maximum | 8% | Pause ALL agents |
| Catastrophic | 10% | Full stop, review |

---

## Risk Enforcement Layers

### Layer 1: Agent Level
Each agent self-enforces:
```python
def check_position_limits(self, proposed_trade):
    position_value = proposed_trade['amount'] * current_price
    portfolio_value = get_portfolio_value()
    
    if position_value / portfolio_value > 0.02:
        return False, "Exceeds 2% rule"
    
    if self.positions_value / portfolio_value > 0.10:
        return False, "Agent at 10% limit"
    
    return True, "OK"
```

### Layer 2: Strategy Level
Strategy coordinator monitors:
- Correlation between strategy positions
- Overexposure to single asset
- Strategy-specific drawdown

### Layer 3: Portfolio Level
Global risk manager:
- Total portfolio exposure
- Cross-strategy correlations
- Daily/weekly P&L limits

### Layer 4: System Level
Final failsafe:
- Hard circuit breaker
- Emergency shutdown
- Manual override capability

---

## Position Sizing

### Kelly Criterion (Modified)
```
f* = (bp - q) / b

Where:
- b = net odds received on winning trades
- p = probability of winning
- q = probability of losing (1-p)

Recommended: Use 25% of Kelly for safety (fractional Kelly)
```

### Risk-Parity Approach
```
Position Size = Portfolio Value * Risk Weight / (ATR * Multiplier)

Example:
- Portfolio: $1000
- Risk Weight: 2%
- ATR(14): $150
- Multiplier: 2

Position = 1000 * 0.02 / (150 * 2) = $1000 * 0.02 / 300 = 0.067
```

### Fixed Fractional
```
Position = Portfolio * Max Risk% / Stop Distance%

Example:
- Portfolio: $1000
- Max Risk: 2%
- Stop Distance: 0.5%

Position = 1000 * 0.02 / 0.005 = $4,000 (capped at portfolio)
→ Use $1000 (portfolio limit)
```

---

## Correlation Management

### Asset Correlation
| Asset Pair | Correlation | Action if High |
|------------|-------------|----------------|
| BTC/ETH | 0.85 | Limit combined exposure |
| BTC/SOL | 0.70 | Moderate |
| ETH/SOL | 0.75 | Moderate |

### Strategy Correlation
- Avoid running same direction on correlated assets
- Hedging: If momentum long BTC, consider scalping short ETH

---

## Monitoring & Alerts

### Real-Time Metrics
```yaml
alert_triggers:
  - name: "High Drawdown"
    condition: "drawdown > 3%"
    severity: "WARNING"
    action: "notify"
    
  - name: "Position Limit Breach"
    condition: "any position > 2%"
    severity: "CRITICAL"
    action: "reject_trade + notify"
    
  - name: "Agent Down"
    condition: "agent heartbeat missing > 60s"
    severity: "CRITICAL"
    action: "restart + notify"
```

### Daily Reports
- P&L by agent, strategy, asset
- Win rate, avg win, avg loss
- Largest drawdown events
- Risk metric summary

---

## Emergency Procedures

### Level 1: Agent Pause
```python
# If single agent exceeds risk
pause_agent(agent_id)
log_event("PAUSED", agent_id, reason)
notify_admin(f"Agent {agent_id} paused: {reason}")
```

### Level 2: Strategy Pause
```python
# If strategy drawdown > threshold
pause_all_agents_in_strategy(strategy)
close_positions_gracefully(strategy)
log_event("STRATEGY_PAUSED", strategy)
```

### Level 3: Full System Pause
```python
# If portfolio drawdown > 8%
pause_all_agents()
set_all_orders_to_cancel()
log_event("SYSTEM_PAUSED", "DRAWDOWN_LIMIT")
send_alert("EMERGENCY STOP - Manual review required")
```

### Level 4: Shutdown
```python
# Only if absolutely necessary
close_all_positions_market()
withdraw_to_cold_storage()
stop_all_agents()
log_event("SYSTEM_SHUTDOWN")
```

---

## Backtesting Validation

Before deploying any strategy, validate:

1. **Historical Drawdown:** Max simulated drawdown < 2x expected
2. **Win Rate:** > 50% for mean reversion, can be lower for momentum
3. **Risk/Reward:** Average win > 1.5x average loss
4. **Correlation:** Strategies don't compound losses
5. **Fee Sensitivity:** Profitable at 1.5x actual fees

---

## Compliance Rules

### Prohibited Actions
- ❌ Wash trading (buying/selling same asset to inflate volume)
- ❌ Trading on material non-public information
- ❌ Exceeding position limits "just this once"
- ❌ Disabling risk controls for "quick profit"
- ❌ Retaining more than 50% in single asset

### Required Logging
- Every trade with timestamp, price, amount, fees
- Every risk override attempt (should be none)
- Every pause/resume event
- Every system alert

---

## Risk Dashboard Metrics

| Metric | Target | Alert |
|--------|--------|-------|
| Daily P&L | > 0% | < -2% |
| Max Position | < 2% | > 2% |
| Max Agent Exposure | < 10% | > 10% |
| Portfolio Drawdown | < 3% | > 5% |
| Sharpe Ratio (monthly) | > 1.5 | < 1.0 |
| Win Rate | > 55% | < 45% |

---

## Summary: Risk Commandments

1. **Thou shalt not risk more than 2% on any trade**
2. **Thou shalt not concentrate more than 10% in any agent**
3. **Thou shalt always set stops on scalping trades**
4. **Thou shalt pause when drawdown exceeds 5%**
5. **Thou shalt review before increasing risk**
6. **Thou shalt log everything**
7. **Thou shalt test strategies before deployment**
8. **Thou shalt respect correlation**
9. **Thou shalt have emergency procedures**
10. **Thou shalt not let greed override discipline**
