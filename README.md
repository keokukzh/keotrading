# KEOTrading - Multi-Agent Crypto Trading System

> 50 specialized trading agents for maximum profit with small capital

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Agents](https://img.shields.io/badge/Agents-50-orange.svg)

## 🎯 Overview

KEOTrading is a sophisticated multi-agent trading system designed to generate consistent profits by orchestrating 50 specialized agents across arbitrage, scalping, grid trading, and momentum strategies. Built on proven open-source foundations with custom orchestration layer.

**Philosophy:** Start small, compound consistently, scale intelligently.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR (Main AI)                  │
│              Koordiniert alle 50 Agenten                    │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐
│ DATA   │  │ RISK   │  │ EXEC   │
│ AGENTS │  │ MGMT   │  │ AGENTS │
│ (10)   │  │ (5)    │  │ (10)   │
└────────┘  └────────┘  └────────┘
    │            │            │
    └────────────┼────────────┘
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  STRATEGY AGENTS (25)                      │
│  • Arbitrage (8)  • Scalping (8)  • Grid (5)  • Momentum (4)
└─────────────────────────────────────────────────────────────┘
```

### Agent Layers

| Layer | Count | Purpose |
|-------|-------|---------|
| **Data Agents** | 10 | Market data collection, orderbook analysis, sentiment tracking |
| **Strategy Agents** | 25 | Trading decisions, arbitrage, scalping, grid, momentum |
| **Execution Agents** | 10 | Order placement, gas optimization, CEX/DEX execution |
| **Risk & Portfolio** | 5 | Position limits, drawdown monitoring, P&L tracking |

---

## 📊 Trading Strategies (Dashboard Selectable)

Choose your strategy from the dashboard:

| Strategy | Risk | Monthly Return | Speed | Best For |
|----------|------|----------------|-------|----------|
| **LP Arbitrage** | Very Low | 3-8% | Fast | Steady gains |
| **Scalping (Mean Rev)** | Medium | 5-15% | Very Fast | Volatile markets |
| **Grid Trading** | Low | 2-5% | Medium | Ranging markets |
| **Momentum** | Medium-High | 10-30% | Slow | Trending markets |
| **DEX Arbitrage** (Solana) | Very Low | 3-8% | Very Fast | Low-cap gems |
| **LLM Enhanced** | Variable | ? | Medium | Qualitative decisions |
| **Hybrid** (Multi-Str) | Medium | 10-20% | All | Balanced |
| **Autopilot** (AI picks) | Variable | ? | AI | Hands-off |

### LP Arbitrage (hzjken Integration)
Uses **Linear Programming** (PULP/CBC) to find optimal multi-lateral arbitrage paths - 10-100x faster than brute force.

### LLM Enhanced (TradingAgents Integration)
Adds **LLM-powered qualitative analysis** using LangGraph for market sentiment, on-chain metrics, and strategy debate.

---

## 🤖 The 50 Agents

### Data Layer (10 Agents)
- 4x Price Monitor (CEX: Binance, Kraken, Coinbase, Bybit)
- 2x Orderbook Analyzer
- 2x News/Sentiment Tracker
- 2x Volume Analyzer

### Strategy Layer (25 Agents)

#### Arbitrage (8)
- 3x Cross-Exchange Arbitrage (Binance↔Kraken↔Coinbase)
- 3x DEX Arbitrage (Solana: Raydium↔Orca↔Marinade)
- 2x Triangle Arbitrage (BTC→ETH→USDT→BTC)

#### Scalping (8)
- 4x Mean Reversion Scalper
- 4x Momentum Scalper

#### Grid (5)
- 5x Grid Bot (different pairs: BTC, ETH, SOL, AVAX, LINK)

#### Momentum (4)
- 4x Trend Follower

### Execution Layer (10 Agents)
- 4x CEX Order Executor
- 4x DEX Order Executor
- 2x Flash Loan Coordinator (Solana)

### Risk & Portfolio (5)
- 2x Risk Manager
- 1x Portfolio Rebalancer
- 1x P&L Tracker
- 1x Compliance Monitor

---

## 🔗 Open Source Integration

This project **combines and extends** the following proven open-source solutions:

| Source | Integration | Purpose |
|--------|-------------|---------|
| [Freqtrade](https://github.com/freqtrade/freqtrade) | Extended | CEX spot & futures trading, strategy framework |
| [Hummingbot](https://github.com/hummingbot/hummingbot) | Reference | Market making, liquidity mining strategies |
| [CCXT](https://github.com/ccxt/ccxt) | Library | Unified exchange API abstraction |
| [Solana Arbitrage Bot](https://github.com/0xNineteen/solana-arbitrage-bot) | Adapted | DEX arbitrage on Solana |
| [AgenticTrading](https://github.com/Open-Finance-Lab/AgenticTrading) | Architecture | Multi-agent orchestration framework |
| [Jesse](https://github.com/jesse-ai/jesse) | Research | Backtesting engine reference |

### How We Merge

```
┌────────────────────────────────────────────────────────────┐
│                    KEOTrading Core                         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Custom Orchestration Layer (our code)                │  │
│  │ • Agent lifecycle management                         │  │
│  │ • Inter-agent communication (Redis Pub/Sub)         │  │
│  │ • Unified strategy coordinator                       │  │
│  │ • Real-time risk scoring                            │  │
│  └─────────────────────────────────────────────────────┘  │
│         ↓                ↓                ↓              │
│   ┌──────────┐    ┌────────────┐    ┌──────────────┐     │
│   │ Freqtrade│    │  CCXT Lib  │    │ Solana Bot   │     │
│   │ (CEX)    │    │ (Abstraction)│   │ (DEX Arb)   │     │
│   └──────────┘    └────────────┘    └──────────────┘     │
└────────────────────────────────────────────────────────────┘
```

**We DON'T fork** - we integrate via:
- **API/CLI** for Freqtrade (runs as service)
- **Library imports** for CCXT
- **Adapted logic** for Solana arbitrage (rewritten for our architecture)
- **Framework patterns** from AgenticTrading (memory, orchestration)

---

## 📊 Dashboard

A comprehensive control center for managing all 50 agents:

```
┌──────────────────────────────────────────────────────────┐
│  KEO TRADING COMMAND CENTER              [P&L: +12.4%]  │
├─────────────┬──────────────┬────────────────────────────┤
│ AGENTS (50)│  PORTFOLIO   │   PERFORMANCE CHART       │
│ [48 Active]│  BTC: 0.45   │   ████████                │
│ [2 Paused] │  ETH: 3.2    │   ████████                │
│            │  SOL: 125    │   ████████                │
├─────────────┴──────────────┴────────────────────────────┤
│ ACTIVE TRADES                                            │
│ • SOL-USDC  Arb    +0.3%   ✓                           │
│ • ETH-BTC   Scalp  +0.8%   ✓                           │
│ • BTC Grid   +1.2%   ⟳                               │
├─────────────────────────────────────────────────────────┤
│ AGENT DETAILS                          [Filter: Arbitrage]│
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Agent #7 (DEX Arb)     Status: RUNNING              │ │
│ │ Pair: SOL/USDC         P&L: +$4.23 today          │ │
│ │ Last Trade: 2min ago    Win Rate: 67%               │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 💰 Trading Strategies

### Phase 1: Capital Building ($100-500)
1. **Solana DEX Arbitrage** - Sub-second, $0.001 fees
2. **Triangle Arbitrage** - 0.1-0.5% per cycle
3. **Grid Trading** - Volatile pairs, 5-10% range

### Phase 2: Scaling ($500-2000)
4. **Cross-Exchange Arbitrage** - Binance, Kraken, Coinbase
5. **Multi-Strategy Freqtrade** - 3-5 strategies parallel

### Phase 3: Growth ($2000+)
6. **Hummingbot Market Making** - Liquidity rewards
7. **Leveraged Scalping** - 2-3x on perps

---

## ⚠️ Risk Management

### Hard Rules (NEVER Break)
- **Max 2%** capital at risk per trade
- **Max 10%** capital in single agent
- **Daily Drawdown Limit:** 5% → pause all agents
- **Weekly Profit Lock:** 5% → hold before reinvesting
- **Always** set hard stop-loss

### Monitoring
- Real-time P&L per agent
- Alerts at 3% drawdown
- Automatic pause on critical events

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Orchestration** | Custom Python + Redis Pub/Sub |
| **CEX Trading** | Freqtrade (extended) |
| **DEX Trading** | Custom Solana bot |
| **Exchange Abstraction** | CCXT |
| **Database** | SQLite + Supabase backup |
| **Dashboard** | Next.js + Tailwind CSS |
| **Monitoring** | Grafana + Prometheus |
| **Container** | Docker + Docker Compose |

---

## 📁 Project Structure

```
keotrading/
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AGENTS.md
│   ├── STRATEGIES.md
│   ├── RISK_MANAGEMENT.md
│   └── OPEN_SOURCE_INTEGRATIONS.md
├── src/
│   ├── orchestrator/         # Main orchestration layer
│   │   ├── agent_manager.py
│   │   ├── communicator.py
│   │   └── scheduler.py
│   ├── agents/               # All 50 agent implementations
│   │   ├── data/
│   │   ├── strategy/
│   │   ├── execution/
│   │   └── risk/
│   ├── strategies/           # Trading strategy implementations
│   │   ├── arbitrage/
│   │   ├── scalping/
│   │   ├── grid/
│   │   └── momentum/
│   ├── exchange/             # Exchange connectors
│   │   ├── cex/              # Freqtrade integration
│   │   └── dex/              # Solana integration
│   └── dashboard/             # Control panel
├── configs/
│   ├── agents.yaml            # Agent configurations
│   ├── risk_limits.yaml       # Risk parameters
│   └── exchanges.yaml        # Exchange API configs
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile
└── scripts/
    ├── setup.sh
    ├── deploy.sh
    └── monitor.sh
```

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/keokukzh/keotrading.git
cd keotrading

# Setup environment
cp configs/exchanges.yaml.example configs/exchanges.yaml
# Edit configs with your API keys

# Start system
docker-compose up -d

# Access dashboard
open http://localhost:3000
```

---

## 📈 Expected Performance

| Phase | Capital | Agents | Monthly Profit |
|-------|---------|--------|----------------|
| 1 | $100 | 5 | $15-30 (15-30%) |
| 2 | $500 | 15 | $50-100 (10-20%) |
| 3 | $2000+ | 50 | $200-400 (10-20%) |

*Conservative estimates. Actual results depend on market conditions.*

---

## 🔬 Development Status

- [x] Architecture design complete
- [ ] Core orchestration layer
- [ ] Agent implementations
- [ ] Dashboard v1
- [ ] Integration with Freqtrade
- [ ] Solana DEX bot
- [ ] Backtesting framework
- [ ] Production deployment

---

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

Built upon the shoulders of giants:
- [Freqtrade](https://github.com/freqtrade/freqtrade)
- [Hummingbot](https://github.com/hummingbot/hummingbot)
- [CCXT](https://github.com/ccxt/ccxt)
- [Solana Arbitrage Bot](https://github.com/0xNineteen/solana-arbitrage-bot)
- [AgenticTrading](https://github.com/Open-Finance-Lab/AgenticTrading)

---

*KEOTrading - Because every bear needs a plan.*
