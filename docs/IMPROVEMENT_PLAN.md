# KEOTrading Dashboard Review & Improvement Plan

**Date:** 2026-04-01  
**Reviewer:** Bobro  
**Version:** 1.0

---

## 📊 CURRENT STATE ASSESSMENT

### ✅ WHAT'S IMPLEMENTED

| Component | Status | Notes |
|-----------|--------|-------|
| **Charts (Plotly)** | ✅ Working | Line charts, pie charts, portfolio distribution |
| **Dashboard UI** | ✅ Working | 5 pages, Streamlit, responsive layout |
| **Strategy Selector** | ✅ Working | 8 strategies with star ratings |
| **Agent Status Display** | ✅ Working | Status table with P&L, uptime |
| **LLM Advisor UI** | ✅ Working | On-chain, sentiment, strategy selector |
| **API Backend** | ✅ Working | FastAPI with endpoints |
| **Config Management** | ✅ Working | Settings page for API keys |

### ❌ WHAT'S MISSING

| Component | Priority | Gap |
|-----------|----------|-----|
| **Live Market Data** | 🔴 CRITICAL | No CCXT WebSocket connections |
| **Real Exchange Connection** | 🔴 CRITICAL | No live trading execution |
| **Exchange Account Linking** | 🔴 CRITICAL | API keys stored but not used |
| **Real-time P&L Updates** | 🔴 CRITICAL | Only mock data |
| **Order Execution** | 🔴 CRITICAL | No actual trade placement |
| **Price Alerts** | 🟡 MEDIUM | No push notifications |
| **Backtesting Engine** | 🟡 MEDIUM | Not connected |
| **Portfolio Real-time Sync** | 🟡 MEDIUM | Static mock positions |

---

## 🔴 CRITICAL GAPS - LIVE TRADING

### Gap 1: No Live Market Data Connection

**Current State:**
```python
# MOCK DATA - Line 35 in 1_Overview.py
def get_mock_pnl_history() -> pd.DataFrame:
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, -1, -1)]
    values = [1000 + i * 50 ...]  # FAKE DATA
```

**Required Implementation:**
```python
# NEEDED: Real CCXT WebSocket connection
import ccxt
import asyncio

class MarketDataStream:
    def __init__(self, exchange_id: str):
        self.exchange = getattr(ccxt, exchange_id)()
        self.ws = None
    
    async def subscribe(self, pairs: List[str]):
        # Connect to exchange WebSocket
        # Subscribe to ticker updates
        # Push to Redis for agents
```

### Gap 2: No Exchange API Integration for Trading

**Current State:**
- API key inputs exist in Settings ✅
- Keys are stored in `configs/exchanges.yaml` ✅
- **BUT: No actual connection or order execution** ❌

**Required Implementation:**
```python
# NEEDED: Real exchange connection
from ccxt import binance

class ExchangeTrader:
    def __init__(self, api_key: str, secret: str):
        self.exchange = binance({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
        })
    
    def place_order(self, symbol: str, side: str, amount: float):
        return self.exchange.create_order(symbol, 'limit', side, amount)
```

### Gap 3: No Real-time Portfolio Sync

**Current State:**
```python
# MOCK - Line 44 in 1_Overview.py
portfolio_data = {
    "Asset": ["USDT", "BTC", "ETH", "SOL", "Other"],
    "Allocation": [45, 25, 15, 10, 5],  # FAKE
}
```

**Required Implementation:**
```python
# NEEDED: Real portfolio from exchanges
async def get_real_portfolio(exchange) -> dict:
    balances = await exchange.fetch_balance()
    total = sum(v for k, v in balances['total'].items() if v > 0)
    # Calculate real allocation
```

---

## 🟡 MEDIUM PRIORITY IMPROVEMENTS

### Improvement 1: Live Charts with Real Data

**Current:** Static mock line chart  
**Needed:** Real-time updating chart with actual P&L

```python
# Add to Overview page
import asyncio
from datetime import datetime

async def update_pnl_chart():
    while True:
        real_pnl = await fetch_real_pnl()
        st.plotly_chart(fig, use_container_width=True)
        await asyncio.sleep(30)  # Refresh every 30s
```

### Improvement 2: Exchange Account Wizard

**Current:** Manual API key entry  
**Needed:** Guided onboarding flow

```
Step 1: Select Exchange (Binance, Kraken, Bybit, etc.)
Step 2: Generate API Key with trading permissions
Step 3: Paste keys into dashboard
Step 4: Test connection
Step 5: Configure which agents can trade
```

### Improvement 3: TradingView Integration

Add embedded TradingView charts for technical analysis:

```python
# In dashboard/pages/4_Portfolio.py
st.components.v1.html("""
<iframe src="https://www.tradingview.com/widget/..."></iframe>
""", height=400)
```

### Improvement 4: Alert System

```python
# Push notifications for trades/alerts
class AlertManager:
    async def send_trade_alert(self, trade: dict):
        # Telegram
        await telegram.send(f"✅ Trade: {trade}")
        # Email
        await email.send_alert(trade)
        # Push
        await push.notify(trade)
```

---

## 📋 PRIORITY IMPROVEMENT ROADMAP

### Phase 1: CRITICAL (Before Any Trading)
- [ ] **CCXT WebSocket Integration** - Live price feeds
- [ ] **Exchange API Connection** - Test connection to Binance/Kraken
- [ ] **Real Portfolio Fetch** - Get actual balances
- [ ] **Real P&L Calculation** - Based on actual trades

### Phase 2: LIVE TRADING (Before Real Money)
- [ ] **Paper Trading Mode** - Simulated execution
- [ ] **Order Execution Engine** - Real order placement
- [ ] **Position Tracking** - Real-time position updates
- [ ] **Trade History** - Actual trade log

### Phase 3: ENHANCEMENTS (After Working System)
- [ ] **TradingView Charts** - Technical analysis widget
- [ ] **Account Onboarding Wizard** - Guided exchange connection
- [ ] **Alert System** - Telegram/Email notifications
- [ ] **Backtesting Integration** - Strategy validation
- [ ] **Multi-Exchange Support** - More exchanges

---

## 🏗️ ARCHITECTURE CHANGES NEEDED

### Add: `src/exchange/connection.py`

```python
"""
Exchange Connection Manager
Handles real exchange connections via CCXT.
"""
from ccxt import binance, kraken, bybit
from typing import Dict, Optional
import asyncio

class ExchangeConnection:
    """Manages live connections to exchanges."""
    
    def __init__(self, exchange_id: str, api_key: str, secret: str):
        self.exchange_id = exchange_id
        self.exchange = self._create_exchange(exchange_id, api_key, secret)
        self.ws_connection = None
    
    def _create_exchange(self, exchange_id: str, api_key: str, secret: str):
        exchange_class = getattr(ccxt, exchange_id)
        return exchange_class({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
    
    async def connect_websocket(self, pairs: List[str]):
        """Connect to exchange WebSocket for live data."""
        # Implementation
        pass
    
    async def fetch_ticker(self, symbol: str) -> dict:
        """Fetch real-time ticker data."""
        return await self.exchange.fetch_ticker(symbol)
    
    async def fetch_balance(self) -> dict:
        """Fetch account balances."""
        return await self.exchange.fetch_balance()
    
    def place_order(self, symbol: str, type: str, side: str, amount: float, price: float = None):
        """Place a real order."""
        return self.exchange.create_order(symbol, type, side, amount, price)
```

### Add: `src/dashboard/real_data.py`

```python
"""
Real-time Data Manager
Replaces mock data with live exchange data.
"""
from exchange.connection import ExchangeConnection
from typing import Dict, List
import asyncio

class RealTimeDataManager:
    """Fetches and caches real market data."""
    
    def __init__(self):
        self.connections: Dict[str, ExchangeConnection] = {}
        self.ticker_cache: Dict[str, dict] = {}
        self.balance_cache: Dict[str, dict] = {}
    
    def add_exchange(self, exchange_id: str, api_key: str, secret: str):
        self.connections[exchange_id] = ExchangeConnection(exchange_id, api_key, secret)
    
    async def get_portfolio_value(self) -> float:
        total = 0
        for conn in self.connections.values():
            balance = await conn.fetch_balance()
            # Calculate USD value
        return total
    
    async def get_agent_pnl(self, agent_id: str) -> dict:
        # Calculate real P&L from trades
        pass
```

---

## 📊 DASHBOARD IMPROVEMENTS

### 1. Live P&L Chart (Overview Page)

Replace mock data:
```python
# OLD (mock)
def get_mock_pnl_history():
    return pd.DataFrame({...})  # fake data

# NEW (real)
async def get_real_pnl_history():
    pnl_data = await real_data_manager.get_pnl_history(days=30)
    return pd.DataFrame(pnl_data)
```

### 2. Real-time Portfolio (Portfolio Page)

```python
# Add refresh button + auto-refresh
if st.button('🔄 Refresh Portfolio'):
    portfolio = await exchange.fetch_balance()
    st.session_state['portfolio'] = portfolio
```

### 3. Exchange Connection Status (Settings)

```python
# Add connection test button
if st.button('🔗 Test Connection'):
    try:
        await exchange.fetch_balance()
        st.success('✅ Connection successful!')
    except Exception as e:
        st.error(f'❌ Connection failed: {e}')
```

---

## 🚀 QUICK WINS

1. **Replace MOCK with REAL** - Use CCXT to fetch real prices
2. **Add Connection Status** - Show which exchanges are connected
3. **Enable Paper Trading Mode** - Flip to simulation
4. **Add "Last Updated" Timestamps** - Show data freshness

---

## 📝 NEXT STEPS

### Immediate (This Session)

1. ✅ Add CCXT as dependency
2. ✅ Create `ExchangeConnection` class
3. ✅ Create `RealTimeDataManager` class  
4. ✅ Add connection test to Settings page
5. ✅ Replace mock P&L with real calculation

### This Week

1. Integrate CCXT WebSocket for live prices
2. Connect to Binance/Kraken testnet
3. Enable paper trading mode
4. Add real-time chart updates

### This Month

1. Full live trading on testnet
2. Multi-exchange support
3. Backtesting integration
4. Alert system (Telegram)
5. Mobile dashboard

---

## 📚 REFERENCES

- [CCXT Documentation](https://docs.ccxt.com/)
- [CCXT WebSocket Guide](https://github.com/ccxt/ccxt/wiki/CCXT)
- [Streamlit Real-time](https://discuss.streamlit.io/t/real-time-updates/1561)
- [Freqtrade WebSocket](https://www.freqtrade.io/en/latest/webhooks/)
