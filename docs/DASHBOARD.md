# KEOTrading Dashboard Documentation

## Overview

The KEOTrading Dashboard is a multi-page Streamlit application providing real-time monitoring, strategy selection, and agent management for the KEOTrading crypto trading system. It integrates with a FastAPI backend and includes an LLM-powered strategy advisor.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│  (app.py + 5 pages: Overview, Strategies, Agents, │
│   Portfolio, Settings)                              │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
                       ▼
┌─────────────────────────────────────────────────────┐
│                FastAPI Backend (api.py)             │
│  /agents, /strategies, /portfolio, /pnl endpoints  │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
  ┌──────────┐  ┌──────────┐  ┌──────────────┐
  │  Agents  │  │ Exchange │  │  LLM Advisor  │
  │   Pool   │  │  APIs    │  │(TradingAgents)│
  └──────────┘  └──────────┘  └──────────────┘
```

---

## Installation

### Prerequisites

- Python 3.10+
- Redis server (optional, for live data)
- Exchange API keys configured in `configs/dashboard.yaml`

### Setup

```bash
# Clone the repository
git clone https://github.com/keokukzh/keotrading.git
cd keotrading

# Install dependencies
pip install -r requirements.txt

# Configure dashboard
cp configs/dashboard.yaml.example configs/dashboard.yaml
# Edit configs/dashboard.yaml with your API keys

# Start the FastAPI backend
python -m uvicorn src.dashboard.api:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start the Streamlit dashboard
streamlit run src/dashboard/app.py --server.port 3000 --server.address 0.0.0.0
```

### Environment Variables

Set these environment variables before starting:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export API_PASSWORD="your-secure-password"
export BINANCE_API_KEY="..."
export BINANCE_SECRET_KEY="..."
```

---

## Pages

### 1. Overview (`/`)
**File:** `src/dashboard/pages/1_Overview.py`

Displays:
- Total P&L metrics (daily, weekly, monthly)
- 30-day P&L line chart
- Portfolio allocation pie chart
- Agent status table with quick actions
- System health metrics (CPU, memory, API latency)

### 2. Strategies (`/strategies`)
**File:** `src/dashboard/pages/2_Strategies.py`

Features:
- 8 trading strategies with star ratings, risk levels, and expected returns
- LLM Strategy Advisor panel (multi-agent debate system)
- Strategy selection with confirmation
- Filterable strategy cards

**Available Strategies:**
| Strategy | Risk | Expected Return |
|---|---|---|
| LP Arbitrage (hzjken) | Medium | 15-25% APR |
| Scalping (Mean Reversion) | Medium-High | 8-15% monthly |
| Grid Trading | Low-Medium | 5-12% monthly |
| Momentum | High | 20-40% |
| DEX Arbitrage (Solana) | Medium | 12-20% monthly |
| LLM Enhanced (TradingAgents) | Medium (adaptive) | Variable |
| Hybrid (Multi-Strategy) | Medium | 10-18% monthly |
| Autopilot (AI picks) | Medium-High (delegated) | Variable |

### 3. Agents (`/agents`)
**File:** `src/dashboard/pages/3_Agents.py`

Features:
- Detailed agent monitoring with filtering and sorting
- Individual agent P&L charts
- Resource usage (CPU, memory) per agent
- Agent control actions (pause, resume, restart, remove)
- Combined P&L summary for filtered agents

### 4. Portfolio (`/portfolio`)
**File:** `src/dashboard/pages/4_Portfolio.py`

Features:
- Portfolio value and allocation metrics
- 30-day portfolio history chart
- Asset allocation pie chart
- Open positions table
- Portfolio drift analysis
- Rebalancing controls

### 5. Settings (`/settings`)
**File:** `src/dashboard/pages/5_Settings.py`

Features:
- LLM provider configuration (OpenAI, Anthropic, Ollama)
- API endpoint settings
- Exchange API key management
- Dashboard preferences (theme, currency, refresh interval)
- Risk limit configuration
- Config export/import

---

## API Endpoints

Base URL: `http://localhost:8000`

### Health
```
GET /health
→ {"status": "healthy", "timestamp": "..."}
```

### Agents
```
GET /agents
  Query params: status, strategy
→ [AgentStatus, ...]

GET /agents/{agent_id}
→ AgentStatus

POST /agents/{agent_id}/start
→ {"success": true, "agent_id": "...", "status": "running"}

POST /agents/{agent_id}/stop
→ {"success": true, "agent_id": "...", "status": "stopped"}

POST /agents
  Body: {"name": "...", "strategy": "..."}
→ AgentStatus
```

### Strategies
```
GET /strategies
→ [Strategy, ...]

GET /strategies/current
→ {"selected": "LP Arbitrage (hzjken)"}

POST /strategies/{strategy_name}/select
→ {"success": true, "selected": "..."}
```

### Portfolio
```
GET /portfolio
→ Portfolio(total_value_usd=100000.0, positions=[...])
```

### P&L
```
GET /pnl?days=30
→ [PnLEntry(date="...", pnl=..., pnl_cumulative=...), ...]

GET /pnl/summary
→ {"total_pnl": 12345.10, "daily_pnl": 432.50, ...}
```

---

## LLM Strategy Advisor

### Overview

The LLM Strategy Advisor uses a **TradingAgents-style multi-agent debate system**:

```
┌─────────────────────────────────────────────────────────┐
│              Multi-Agent Debate Pipeline                │
│                                                         │
│  1. On-Chain Analyst ───────────────────┐                │
│     (TVL, DEX volume, gas fees)         │                │
│                                         ▼                │
│                              ┌───────────────────┐      │
│                              │ Strategy Selector  │      │
│                              │   (LLM-powered)    │      │
│                              └───────────────────┘      │
│                                         │                │
│  2. Sentiment Analyst ──────────────┘                   │
│     (Social, funding rates, positioning)                │
│                                                         │
│  Output: recommended_strategy + confidence + reasoning │
└─────────────────────────────────────────────────────────┘
```

### Configuration

Edit `configs/dashboard.yaml`:

```yaml
llm:
  provider: "openai"           # openai, anthropic, ollama
  model: "gpt-4o"
  temperature: 0.7
  max_tokens: 2048
```

### Providers

**OpenAI:**
- Set `OPENAI_API_KEY` environment variable
- Models: gpt-4o, gpt-4-turbo, gpt-3.5-turbo

**Anthropic:**
- Set `ANTHROPIC_API_KEY` environment variable
- Models: claude-opus-4, claude-sonnet-4, claude-haiku

**Ollama (local):**
- Set `OLLAMA_BASE_URL` (default: http://localhost:11434)
- Models: llama3.3, mistral, codellama

### Output

The advisor returns:
- `recommended_strategy`: Best strategy for current conditions
- `confidence`: 0-100 confidence score
- `reasoning`: Human-readable explanation
- `debate_log`: Full multi-agent conversation transcript

---

## Dashboard Components

Located in `src/dashboard/components/`:

| Component | Description |
|---|---|
| `agent_card.py` | Reusable agent status card with metrics and actions |
| `pnl_chart.py` | P&L line, bar, and cumulative area charts |
| `strategy_card.py` | Strategy selection card with star ratings |
| `portfolio_pie.py` | Portfolio allocation pie/bar charts |

### Using Components

```python
from src.dashboard.components.agent_card import render_agent_card

agent_data = {
    "id": "agent-001",
    "name": "Hzjken LP Agent",
    "strategy": "LP Arbitrage",
    "status": "running",
    "pnl": 4521.30,
    # ...
}
render_agent_card(agent_data)
```

---

## Development

### Running in Development

```bash
# Start backend with auto-reload
uvicorn src.dashboard.api:app --reload --port 8000

# Start frontend with auto-reload
streamlit run src/dashboard/app.py --server端口 3000
```

### Adding New Strategies

1. Add strategy definition to `src/dashboard/pages/2_Strategies.py` in `STRATEGIES` list
2. Add to API `STRATEGIES_DB` in `src/dashboard/api.py`
3. Update `configs/dashboard.yaml` if needed

### Adding New Dashboard Pages

1. Create `src/dashboard/pages/N_PageName.py`
2. Import `from __future__ import annotations` and `import streamlit as st`
3. Add a `render_page()` function
4. Streamlit auto-discovers pages in the `pages/` directory

---

## Troubleshooting

**Streamlit page not found:**
Ensure pages are in `src/dashboard/pages/` with numeric prefixes.

**API connection errors:**
Verify the FastAPI backend is running on port 8000.

**LLM advisor not working:**
Check API key environment variables and provider configuration.

**Exchange errors:**
Verify API keys in `configs/dashboard.yaml` or environment variables.

---

## License

See project root LICENSE file.
