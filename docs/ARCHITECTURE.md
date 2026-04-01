# KEOTrading Architecture

## System Overview

KEOTrading is a multi-agent crypto trading system built on Python 3.11+ that orchestrates 50 autonomous trading agents communicating via Redis Pub/Sub.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           KEOTrading System                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐                                                       │
│  │  Scheduler   │ ─── Schedules & routes messages                        │
│  └──────────────┘                                                       │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                    Orchestrator                              │       │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │       │
│  │  │AgentManager │ │Communicator │ │    RiskEnforcer         │ │       │
│  │  │             │ │             │ │                         │ │       │
│  │  │ • lifecycle │ │ • Redis     │ │ • 2% per trade max      │ │       │
│  │  │ • health    │ │   Pub/Sub   │ │ • 10% per agent max     │ │       │
│  │  │ • restart   │ │ • routing   │ │ • 5% daily loss limit   │ │       │
│  │  └─────────────┘ └─────────────┘ └─────────────────────────┘ │       │
│  └─────────────────────────────────────────────────────────────┘       │
│         │                              │                                 │
│         ▼                              ▼                                 │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                    Message Bus (Redis)                         │     │
│  └────────────────────────────────────────────────────────────────┘     │
│         │         │         │         │         │                       │
│         ▼         ▼         ▼         ▼         ▼                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐       │
│  │  Data   │ │Strategy │ │Execution│ │  Risk   │ │   System    │       │
│  │ Agents  │ │ Agents  │ │ Agents  │ │ Agents  │ │   Agent     │       │
│  │   (10)  │ │  (25)   │ │  (10)   │ │   (5)   │ │             │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────┘       │
│       │           │           │           │                             │
│       ▼           ▼           ▼           ▼                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
│  │ • Price │ │ • Arbit │ │ • CEX   │ │ • Risk  │                       │
│  │   Monitor│ │ • Scalp │ │   Exec  │ │   Mgr   │                       │
│  │ • Order │ │ • Grid   │ │ • DEX   │ │ • Port  │                       │
│  │   book  │ │ • Momentum│ │   Exec  │ │   Rebal │                       │
│  │ • Volume│ │         │ │ • Flash │ │ • PnL   │                       │
│  │ • Senti │ │         │ │   Loan  │ │   Track │                       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                     External Systems                            │     │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │     │
│  │  │ Binance │ │ Coinbase│ │  Solana │ │ Ethereum│              │     │
│  │  │   CEX   │ │   CEX   │ │  DEX    │ │  DEX    │              │     │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘              │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Agent Types

### Data Agents (10)
Collect and distribute market data to other agents.

| Agent | Count | Purpose |
|-------|-------|---------|
| PriceMonitor | 2 | Real-time price tracking |
| OrderbookAnalyzer | 2 | Order book depth analysis |
| SentimentTracker | 2 | Social/news sentiment |
| VolumeAnalyzer | 2 | Volume patterns |
| FundingRateMonitor | 1 | Funding rate monitoring |
| LiquidationTracker | 1 | Liquidation detection |

### Strategy Agents (25)
Generate trading signals based on market analysis.

| Strategy | Count | Purpose |
|----------|-------|---------|
| Arbitrage | 5 | Cross-exchange, triangular arbitrage |
| Scalping | 5 | Quick in-and-out trades |
| Grid | 5 | Grid trading |
| Momentum | 10 | Trend following, mean reversion |

### Execution Agents (10)
Execute orders on exchanges.

| Agent | Count | Purpose |
|-------|-------|---------|
| CEXExecutor | 5 | Centralized exchanges (Binance, Coinbase, Kraken, Bybit) |
| DEXExecutor | 4 | Decentralized exchanges (Raydium, Orca, Uniswap) |
| FlashLoanCoordinator | 1 | Flash loan orchestration |

### Risk Agents (5)
Monitor and enforce risk limits.

| Agent | Count | Purpose |
|-------|-------|---------|
| RiskManager | 1 | Primary risk enforcement |
| PortfolioRebalancer | 1 | Portfolio allocation |
| PnLTracker | 1 | Profit/loss tracking |
| ComplianceMonitor | 1 | Trading rules compliance |
| EmergencyStop | 1 | Emergency shutdown |

## Agent Lifecycle States

```
                    ┌─────────────┐
                    │   STOPPED   │ ◄────────── Initial state
                    └──────┬──────┘
                           │ start()
                           ▼
                    ┌────────────────┐
             ┌──────│ INITIALIZING   │
             │      └───────┬────────┘
             │              │ on_start() completes
             │              ▼
             │      ┌───────────────┐
             │      │    RUNNING    │──────────┐
             │      └───────┬───────┘          │
             │              │                  │ pause()
             │              │                  ▼
             │              │           ┌───────────┐
             │              │           │  PAUSED   │
             │              │           └─────┬─────┘
             │              │                 │ resume()
             │              │                 │
             │              │     ┌───────────┴────────┐
             │              │     │                   │
             │              ▼     ▼                   │
             │      ┌───────────────┐                  │
             │      │    FAILED     │                  │
             │      └───────┬───────┘                  │
             │              │                          │
             │              │ restart()                │
             │              ▼                          │
             │      ┌───────────────┐                  │
             └──────│  RESTARTING  │──────────────────┘
                    └───────────────┘
                           │
                           │ stop()
                           ▼
                    ┌───────────────┐
                    │   STOPPING    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌─────────────┐
                    │   STOPPED   │
                    └─────────────┘
```

## Communication Patterns

### Redis Pub/Sub Channels

```
Channel: keotrading:events
├── purpose: System-wide events
├── message_types: agent_started, agent_stopped, agent_failed
└── subscribers: All agents

Channel: keotrading:trades
├── purpose: Trade execution updates
├── message_types: order_submitted, order_executed, order_failed, order_cancelled
└── subscribers: Strategy agents, Risk agents

Channel: keotrading:risk
├── purpose: Risk management updates
├── message_types: trade_approved, risk_alert, limit_reached
└── subscribers: All trading agents

Channel: keotrading:data
├── purpose: Market data distribution
├── message_types: data_update, price_update, orderbook_update
└── subscribers: Strategy agents

Channel: keotrading:strategy
├── purpose: Strategy signals and coordination
├── message_types: execute_signal, signal_generated
└── subscribers: Execution agents

Channel: keotrading:system
├── purpose: System health and control
├── message_types: health_check, shutdown, emergency_stop
└── subscribers: Orchestrator, Risk agents

Channel: keotrading:alerts
├── purpose: Risk alerts and warnings
├── message_types: risk_alert, breach_alert, emergency_stop
└── subscribers: Risk agents, System
```

### Direct Agent Messages

```
┌─────────────┐                        ┌─────────────┐
│   Agent A   │ ─── send_direct() ──► │   Agent B   │
│             │ ◄── response ───────── │             │
└─────────────┘                        └─────────────┘

Used for:
- Task assignments
- Direct queries
- Request/response patterns
```

### Message Priority

| Priority | Value | Use Case |
|----------|-------|----------|
| LOW | 1 | Data updates, heartbeats |
| NORMAL | 2 | Standard operations |
| HIGH | 3 | Trade signals, alerts |
| CRITICAL | 4 | Emergency stops, breaches |

## Risk Enforcement Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Risk Enforcement Pipeline                        │
└─────────────────────────────────────────────────────────────────────┘

Strategy Agent                    RiskEnforcer                    Execution
      │                                │                               │
      │ ── generate signal ──────────► │                               │
      │                                │                               │
      │                                ▼                               │
      │                    ┌───────────────────────┐                 │
      │                    │   Validate Trade       │                 │
      │                    │                        │                 │
      │                    │ 1. Check trade size    │                 │
      │                    │    (2% max per trade)  │                 │
      │                    │                        │                 │
      │                    │ 2. Check agent         │                 │
      │                    │    exposure (10% max)   │                 │
      │                    │                        │                 │
      │                    │ 3. Check portfolio     │                 │
      │                    │    exposure (100% max) │                 │
      │                    │                        │                 │
      │                    │ 4. Check leverage     │                 │
      │                    │    (5x max)            │                 │
      │                    │                        │                 │
      │                    │ 5. Check daily loss   │                 │
      │                    │    (5% max)            │                 │
      │                    │                        │                 │
      │                    │ 6. Check drawdown      │                 │
      │                    │    (15% max)           │                 │
      │                    └───────────────────────┘                 │
      │                                │                               │
      │    ┌───────────────────────────┴───────────────────────────┐  │
      │    │                                                       │  │
      │    ▼                                                       ▼  │
      │ ┌──────────────┐                              ┌──────────────┐│
      │ │   APPROVED   │                              │   REJECTED   ││
      │ │ (with/w-out  │                              │              ││
      │ │ conditions)  │                              │              ││
      │ └──────┬───────┘                              └──────────────┘│
      │        │                                                        │
      │        ▼                                                        │
      │ ────── approve_trade() ────────────────────────────────►       │
      │                                                              │   │
      │                                                              ▼   │
      │                                                    ┌────────────┐│
      │                                                    │  Execute   ││
      │                                                    │  Order     ││
      │                                                    └─────┬──────┘│
      │                                                          │       │
      │    record_trade_result() ◄─────────────────────────────┘       │
      │                                                              │   │
      │        ◄── broadcast trade_executed ──────────────────────────┘
      │                                                              │
      ▼
┌──────────────┐
│  Update      │
│  Positions   │
└──────────────┘
```

### Risk Limits Summary

| Limit | Value | Applies To |
|-------|-------|------------|
| Max trade size | 2% of portfolio | Per trade |
| Max agent exposure | 10% of portfolio | Per agent |
| Max portfolio exposure | 100% of portfolio | Total |
| Max leverage | 5x | Per trade |
| Max daily loss | 5% of portfolio | Daily |
| Max drawdown | 15% of portfolio | Rolling |

## Docker Services

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose Stack                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐      ┌─────────────┐                       │
│  │    Redis    │      │ Prometheus  │                       │
│  │   (6379)    │      │   (9090)    │                       │
│  └─────────────┘      └─────────────┘                       │
│         │                    │                               │
│         │                    ▼                               │
│         │             ┌─────────────┐                        │
│         │             │  Grafana    │                        │
│         │             │  (3030)     │                        │
│         │             └─────────────┘                        │
│         │                    │                               │
│         └──────────┬─────────┘                               │
│                    │                                          │
│                    ▼                                          │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              Orchestrator (Main App)                │     │
│  │              Port: 8000 (API)                       │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
keotrading/
├── src/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── agent_manager.py    # Agent lifecycle management
│   │   ├── communicator.py     # Redis Pub/Sub
│   │   ├── risk_enforcer.py    # Risk limits enforcement
│   │   └── scheduler.py        # Task scheduling
│   │
│   └── agents/
│       └── base/
│           ├── __init__.py
│           ├── base_agent.py       # Abstract base
│           ├── data_agent.py        # Data collection
│           ├── strategy_agent.py    # Trading strategies
│           ├── execution_agent.py   # Order execution
│           └── risk_agent.py        # Risk monitoring
│
├── configs/
│   └── agents.yaml             # All 50 agent configurations
│
├── docker/
│   ├── docker-compose.yml      # Full stack deployment
│   ├── Dockerfile              # App container
│   ├── prometheus.yml          # Metrics config
│   └── grafana/                # Dashboard provisioning
│
├── docs/
│   └── ARCHITECTURE.md         # This file
│
├── requirements.txt            # Python dependencies
└── README.md                   # Setup instructions
```

## Dependencies

### Core
- `ccxt` - Unified exchange API
- `redis` - Message broker
- `pandas`, `numpy` - Data processing

### Solana/DEX
- `solana` - Solana blockchain
- `raydium`, `orca` - DEX protocols

### Monitoring
- `prometheus-client` - Metrics
- `prometheus`, `grafana` - Docker containers
