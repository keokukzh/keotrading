# Open Source Integrations

This document details how KEOTrading combines and extends existing open-source projects.

## Philosophy

We **integrate, not fork**. Instead of forking repositories (which creates maintenance nightmares), we:
1. Run services via API/CLI (Freqtrade)
2. Import libraries (CCXT)
3. Adapt patterns (Solana bot logic)
4. Reference architectures (AgenticTrading)

---

## Freqtrade Integration

**Repository:** https://github.com/freqtrade/freqtrade

### How We Use It
- Runs as a **sidecar service** via Docker
- Controlled via REST API from our orchestrator
- Strategies developed with Freqtrade framework, deployed to its ecosystem
- Pairs lists, stake amounts, and trade execution managed externally

### What We Extend
- Custom hyperopt parameters for our 50-agent system
- Additional plot capabilities for multi-agent visualization
- Enhanced telegram integration for agent-specific alerts

### Integration Code
```python
# Our orchestrator communicates with Freqtrade
import requests

FREQTRADE_URL = "http://freqtrade:8080"

def execute_trade(agent_id, pair, side, amount):
    # Delegate to Freqtrade for CEX execution
    payload = {
        "pair": pair,
        "side": side,
        "amount": amount,
        "agent_id": agent_id  # Our metadata
    }
    requests.post(f"{FREQTRADE_URL}/api/v1/trade", json=payload)
```

---

## Hummingbot Reference

**Repository:** https://github.com/hummingbot/hummingbot

### How We Reference It
- **Market making strategies** - we study their MM algorithms for liquidity mining
- **Connector architecture** - inspiration for our exchange abstraction
- ** liquidity mining rewards** calculation - adapted for our portfolio

### What We Don't Use
We don't run Hummingbot directly (complexity), but we:
- Monitor Hummingbot bounty channels for market opportunities
- Adapt MM logic into our scalping agents

---

## CCXT Library

**Repository:** https://github.com/ccxt/ccxt

### How We Use It
Core exchange abstraction - **required dependency**:
```python
import ccxt

# Unified interface to all exchanges
exchange = ccxt.binance()
orders = exchange.fetch_order_book('BTC/USDT')

# Our agents use this exclusively for market data
```

### Why CCXT
- 100+ exchange implementations
- Unified API across CEX and DEX
- Active maintenance
- Battle-tested in production

---

## Solana Arbitrage Bot

**Repository:** https://github.com/0xNineteen/solana-arbitrage-bot

### How We Adapt It
We **rewrite the core logic** for our architecture:

| Original | KEOTrading Adaptation |
|----------|---------------------|
| Standalone Python script | Modular agent class |
| Hardcoded pools | Dynamic pool discovery |
| Single-threaded | Multi-agent parallel |
| Basic logging | Redis pub/sub for monitoring |

### Core Logic We Keep
- Triangle arbitrage detection algorithm
- Jupiter/Serum API integration patterns
- Fee calculation for Solana txs

### DEX Connectors
- Raydium (Solana AMM)
- Orca (Solana DEX)
- Marinade Finance (liquid staking)

---

## AgenticTrading Framework

**Repository:** https://github.com/Open-Finance-Lab/AgenticTrading

### Architecture Patterns We Adopt

```
┌─────────────────────────────────────────────────────────┐
│                    OUR IMPLEMENTATION                   │
├─────────────────────────────────────────────────────────┤
│  FinAgent Orchestration    →  Our Orchestrator          │
│  Memory Agent              →  Our Redis + SQLite        │
│  Data Agent Pool           →  Our 10 Data Agents       │
│  Alpha Agent Pool          →  Our 25 Strategy Agents  │
│  Execution Agent Pool      →  Our 10 Execution Agents   │
│  Risk Agent                →  Our 5 Risk Agents         │
└─────────────────────────────────────────────────────────┘
```

### What We Improve
- **Lighter weight** - no Neo4j dependency (we use SQLite + Redis)
- **Simpler deployment** - Docker Compose instead of K8s
- **More agents** - 50 vs their ~10 specialized agents
- **Real trading focus** - not just research

---

## Jesse (Reference)

**Repository:** https://github.com/jesse-ai/jesse

### How We Reference It
- **Backtesting engine** - we study their tick-data backtesting for accuracy
- **Strategy syntax** - familiar pattern for strategy development
- **蜡烛图 patterns** - candle pattern recognition

### Why Not Use Directly
Jesse is excellent but:
- More focused on backtesting than live trading
- Fewer exchange connectors than CCXT
- We prefer Freqtrade's live trading ecosystem

---

## Integration Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     KEOTrading System                          │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              ORCHESTRATOR (Main Controller)              │  │
│  │  • Schedules 50 agents                                   │  │
│  │  • Routes messages via Redis Pub/Sub                     │  │
│  │  • Enforces risk limits                                  │  │
│  │  • Aggregates P&L reporting                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                 │
│         ┌────────────────────┼────────────────────┐          │
│         ▼                    ▼                    ▼          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  DATA (10)  │    │STRATEGY (25)│    │ EXEC (10)  │      │
│  │             │    │             │    │             │      │
│  │ • CCXT      │    │ • Freqtrade │    │ • CCXT      │      │
│  │ • Websockets│    │ • Custom    │    │ • Solana    │      │
│  │ • APIs      │    │   Solana    │    │   SDK       │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│                             │                                 │
│                             ▼                                 │
│                    ┌─────────────────┐                       │
│                    │  RISK (5)       │                       │
│                    │  • Position monitoring                  │
│                    │  • Drawdown enforcement                │
│                    │  • Stop-loss execution                 │
│                    └─────────────────┘                       │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Market Data Flow
```
Exchange Websockets → Data Agents → Redis → Strategy Agents
                                        ↓
                               Decision Made
                                        ↓
                              Execution Agent → Exchange
                                        ↓
                              Risk Agent → Verify
```

### Trade Execution Flow
```
Strategy Agent → "BUY 0.1 BTC" → Orchestrator → Execution Agent
                                        ↓
                              Risk Check (2% limit)
                                        ↓
                              CCXT/Solana SDK → Exchange
                                        ↓
                              Confirmation → P&L Tracker
```

---

## External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| ccxt | 4.x | Exchange abstraction |
| freqtrade | 2024.x | CEX trading (sidecar) |
| solana | 0.30.x | Solana blockchain |
| raydium | latest | Solana DEX |
| redis | 5.x | Inter-agent messaging |
| sqlalchemy | 2.x | Database |
| pandas | 2.x | Data processing |
| numpy | 1.26.x | Calculations |

---

## Contributing Integrations

When adding a new exchange or strategy:

1. **CEX:** Use CCXT - if missing, contribute upstream
2. **DEX:** Build adapter pattern - see Solana example
3. **Strategy:** Implement base class, register with orchestrator
4. **Data Source:** Create Data Agent, publish to Redis channel

---

## License Compatibility

All integrated projects are MIT or Apache 2.0 - fully compatible with KEOTrading's MIT license.
