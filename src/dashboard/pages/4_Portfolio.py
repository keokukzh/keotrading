"""
KEOTrading Dashboard - Portfolio Page
====================================
Portfolio management, allocation, position tracking, and trade execution.
"""

from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path
import requests
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# Configuration
API_BASE_URL = "http://localhost:8080"


def get_api_url():
    """Get API base URL from session state."""
    return st.session_state.get('api_url', API_BASE_URL)


def get_mock_positions() -> List[Dict[str, Any]]:
    """Return mock position data."""
    return [
        {"id": "POS-001", "asset": "BTC", "amount": 0.85, "value_usd": 54400, "allocation": 0.34, "entry_price": 62000, "current_price": 64000, "pnl": 1700, "source": "Binance", "strategy": "Momentum"},
        {"id": "POS-002", "asset": "ETH", "amount": 8.5, "value_usd": 28900, "allocation": 0.18, "entry_price": 3300, "current_price": 3400, "pnl": 850, "source": "Binance", "strategy": "Scalping"},
        {"id": "POS-003", "asset": "SOL", "amount": 150.0, "value_usd": 22500, "allocation": 0.14, "entry_price": 140, "current_price": 150, "pnl": 1500, "source": "Solana DEX", "strategy": "DEX Arbitrage"},
        {"id": "POS-004", "asset": "USDT", "amount": 35000.0, "value_usd": 35000, "allocation": 0.22, "entry_price": 1.0, "current_price": 1.0, "pnl": 0, "source": "Binance", "strategy": "Reserve"},
        {"id": "POS-005", "asset": "LINK", "amount": 200.0, "value_usd": 3000, "allocation": 0.02, "entry_price": 14, "current_price": 15, "pnl": 200, "source": "Binance", "strategy": "Grid"},
        {"id": "POS-006", "asset": "AVAX", "amount": 100.0, "value_usd": 3200, "allocation": 0.02, "entry_price": 30, "current_price": 32, "pnl": 200, "source": "Bybit", "strategy": "Momentum"},
        {"id": "POS-007", "asset": "RAY", "amount": 2000.0, "value_usd": 2400, "allocation": 0.015, "entry_price": 1.1, "current_price": 1.2, "pnl": 200, "source": "Raydium LP", "strategy": "LP Arbitrage"},
        {"id": "POS-008", "asset": "ORCA", "amount": 1500.0, "value_usd": 2100, "allocation": 0.013, "entry_price": 1.3, "current_price": 1.4, "pnl": 150, "source": "Orca LP", "strategy": "LP Arbitrage"},
    ]


def get_mock_history() -> pd.DataFrame:
    """Return mock portfolio history."""
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, -1, -1)]
    values = []
    running = 120000
    for i in range(31):
        change = (i % 3 - 1) * 500 + (i % 7) * 200 + (i % 5) * 100
        running += change
        values.append(running)
    return pd.DataFrame({"date": dates, "value": values})


def fetch_api_positions() -> Optional[List[Dict]]:
    """Try to fetch real positions from API."""
    try:
        response = requests.get(f"{get_api_url()}/trading/positions", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def fetch_api_trades() -> Optional[List[Dict]]:
    """Try to fetch real trades from API."""
    try:
        response = requests.get(f"{get_api_url()}/trading/trades", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def place_order_via_api(exchange_id: str, symbol: str, side: str, order_type: str, amount: float, price: float = None) -> Optional[Dict]:
    """Place order via API."""
    try:
        payload = {
            "exchange_id": exchange_id,
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "amount": amount,
            "price": price
        }
        response = requests.post(f"{get_api_url()}/trading/orders", json=payload, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def render_portfolio() -> None:
    """Render the Portfolio page."""
    st.title("💼 Portfolio Management")
    st.markdown("Track your portfolio allocation, positions, and performance.")
    st.markdown("---")

    # Try to get real data from API, fall back to mock
    real_positions = fetch_api_positions()
    real_trades = fetch_api_trades()
    
    positions = real_positions if real_positions else get_mock_positions()
    history = get_mock_history()
    total_value = sum(p.get("value_usd", 0) for p in positions)
    total_pnl = sum(p.get("pnl", 0) for p in positions)

    # Mode indicator
    if real_positions:
        st.success("🟢 LIVE DATA - Connected to Exchange")
    else:
        st.info("📝 DEMO MODE - Connect API in Settings for live data")

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        delta_pct = (total_pnl / (total_value - total_pnl)) * 100 if total_value > total_pnl else 0
        st.metric("Total Value", f"${total_value:,.2f}", delta=f"{total_pnl:+.2f} ({delta_pct:+.2f}%)")
    with col2:
        st.metric("Assets", f"{len(positions)}")
    with col3:
        # Calculate 24h change (mock)
        change_24h = total_value * 0.005  # 0.5% mock
        st.metric("24h Change", f"+${change_24h:,.2f}", delta="+0.54%")
    with col4:
        # Calculate 7d change (mock)
        change_7d = total_value * 0.03  # 3% mock
        st.metric("7d Change", f"+${change_7d:,.2f}", delta="+3.21%")

    st.markdown("---")

    # Charts
    chart_col1, chart_col2 = st.columns([1, 1])

    with chart_col1:
        st.subheader("📈 Portfolio History (30d)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=history["date"],
            y=history["value"],
            mode="lines",
            fill="tozeroy",
            line=dict(color="#4ECDC4", width=2),
            fillcolor="rgba(78, 205, 196, 0.1)",
            name="Value"
        ))
        fig.update_layout(
            height=320,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", tickprefix="$"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        st.subheader("🥧 Asset Allocation")
        pie_data = {
            "asset": [p["asset"] for p in positions[:8]],
            "value": [p["value_usd"] for p in positions[:8]],
        }
        colors = ["#00D4AA", "#FF6B6B", "#4ECDC4", "#FFD93D", "#95A5A6", "#6C5CE7", "#A29BFE", "#FD79A8"]
        pie_fig = px.pie(
            pie_data,
            values="value",
            names="asset",
            hole=0.5,
            color_discrete_sequence=colors,
        )
        pie_fig.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(pie_fig, use_container_width=True)

    st.markdown("---")

    # New Order Section
    st.subheader("📝 Place New Order")
    
    order_col1, order_col2, order_col3, order_col4 = st.columns([1, 1, 1, 1])
    
    with order_col1:
        exchange = st.selectbox("Exchange", ["binance", "kraken", "bybit", "coinbase"], key="order_exchange")
    
    with order_col2:
        symbol = st.selectbox("Pair", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "LINK/USDT"], key="order_symbol")
    
    with order_col3:
        side = st.radio("Side", ["BUY", "SELL"], horizontal=True, key="order_side")
    
    with order_col4:
        order_type = st.selectbox("Type", ["MARKET", "LIMIT"], key="order_type")
    
    amount_col1, amount_col2 = st.columns([1, 1])
    
    with amount_col1:
        amount = st.number_input("Amount", min_value=0.001, value=0.1, step=0.01, key="order_amount")
    
    with amount_col2:
        if order_type == "LIMIT":
            price = st.number_input("Price", min_value=0.01, value=64000.0, step=100.0, key="order_price")
        else:
            price = None
    
    if st.button("🚀 Place Order", type="primary", use_container_width=True):
        with st.spinner("Placing order..."):
            result = place_order_via_api(exchange, symbol, side.lower(), order_type.lower(), amount, price)
            if result:
                st.success(f"✅ Order placed: {result.get('order_id', 'N/A')}")
            else:
                st.info("📝 Order simulated (API not connected)")
    
    st.markdown("---")

    # Positions Table
    st.subheader("📊 Open Positions")
    
    # Filter
    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])
    
    with filter_col1:
        filter_exchange = st.selectbox("Filter Exchange", ["All", "Binance", "Kraken", "Bybit", "Solana DEX"], key="filter_exchange")
    
    with filter_col2:
        filter_strategy = st.selectbox("Filter Strategy", ["All", "Momentum", "Scalping", "Grid", "DEX Arbitrage", "LP Arbitrage"], key="filter_strategy")
    
    with filter_col3:
        st.write("")
    
    # Filter positions
    filtered_positions = positions
    if filter_exchange != "All":
        filtered_positions = [p for p in filtered_positions if p.get("source", "").startswith(filter_exchange)]
    if filter_strategy != "All":
        filtered_positions = [p for p in filtered_positions if p.get("strategy", "") == filter_strategy]
    
    # Table header
    header_cols = st.columns([2, 1, 1, 1, 1, 1, 1])
    headers = ["Asset", "Amount", "Value", "Entry", "Current", "P&L", "Actions"]
    for i, h in enumerate(headers):
        with header_cols[i]:
            st.markdown(f"**{h}**")
    
    st.markdown("---")
    
    # Position rows
    for pos in filtered_positions:
        pnl_color = "green" if pos.get("pnl", 0) >= 0 else "red"
        
        row_cols = st.columns([2, 1, 1, 1, 1, 1, 1])
        
        with row_cols[0]:
            st.markdown(f"**{pos['asset']}**")
            st.caption(f"{pos.get('source', 'Unknown')} • {pos.get('strategy', 'Unknown')}")
        
        with row_cols[1]:
            st.write(f"{pos['amount']:.4f}")
        
        with row_cols[2]:
            st.write(f"${pos['value_usd']:,.2f}")
        
        with row_cols[3]:
            st.write(f"${pos.get('entry_price', 0):,.2f}")
        
        with row_cols[4]:
            st.write(f"${pos.get('current_price', 0):,.2f}")
        
        with row_cols[5]:
            st.markdown(f"<span style='color:{pnl_color}'>${pos.get('pnl', 0):+,.2f}</span>", unsafe_allow_html=True)
        
        with row_cols[6]:
            action_cols = st.columns(2)
            with action_cols[0]:
                if st.button("📈", key=f"tp_{pos['id']}", help="Set Take Profit"):
                    st.info("Take Profit coming soon")
            with action_cols[1]:
                if st.button("🛑", key=f"sl_{pos['id']}", help="Set Stop Loss"):
                    st.info("Stop Loss coming soon")
        
        st.markdown("---")
    
    # Summary
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    with summary_col1:
        total_invested = sum(p['entry_price'] * p['amount'] for p in filtered_positions)
        st.metric("Total Invested", f"${total_invested:,.2f}")
    with summary_col2:
        st.metric("Current Value", f"${sum(p['value_usd'] for p in filtered_positions):,.2f}")
    with summary_col3:
        total_pnl_filtered = sum(p.get('pnl', 0) for p in filtered_positions)
        st.metric("Total P&L", f"${total_pnl_filtered:+,.2f}", delta_color="normal" if total_pnl_filtered >= 0 else "inverse")
    
    st.markdown("---")
    
    # Recent Trades
    st.subheader("📜 Recent Trades")
    
    # Fetch trades
    trades = real_trades if real_trades else []
    
    if not trades:
        # Mock trades
        trades = [
            {"id": "TRD-001", "time": "14:32:05", "pair": "BTC/USDT", "side": "BUY", "amount": 0.1, "price": 63800, "fee": 6.38},
            {"id": "TRD-002", "time": "13:15:22", "pair": "ETH/USDT", "side": "SELL", "amount": 2.0, "price": 3420, "fee": 6.84},
            {"id": "TRD-003", "time": "12:45:11", "pair": "SOL/USDT", "side": "BUY", "amount": 50.0, "price": 148, "fee": 7.40},
            {"id": "TRD-004", "time": "11:22:33", "pair": "AVAX/USDT", "side": "BUY", "amount": 25.0, "price": 31.5, "fee": 7.88},
            {"id": "TRD-005", "time": "10:05:44", "pair": "LINK/USDT", "side": "SELL", "amount": 100.0, "price": 14.8, "fee": 14.80},
        ]
    
    trades_col1, trades_col2, trades_col3, trades_col4, trades_col5, trades_col6 = st.columns([1, 1, 1, 1, 1, 1])
    
    for i, h in enumerate(["Time", "Pair", "Side", "Amount", "Price", "Fee"]):
        with [trades_col1, trades_col2, trades_col3, trades_col4, trades_col5, trades_col6][i]:
            st.markdown(f"**{h}**")
    
    st.markdown("---")
    
    for trade in trades[:10]:
        side_color = "green" if trade.get("side", "").upper() == "BUY" else "red"
        side_icon = "🟢" if trade.get("side", "").upper() == "BUY" else "🔴"
        
        row_cols = st.columns([1, 1, 1, 1, 1, 1])
        
        with row_cols[0]:
            st.write(trade.get("time", trade.get("executed_at", "N/A")[:19]))
        with row_cols[1]:
            st.write(trade.get("pair", trade.get("symbol", "N/A")))
        with row_cols[2]:
            st.markdown(f"{side_icon} {trade.get('side', 'N/A').upper()}")
        with row_cols[3]:
            st.write(f"{trade.get('amount', 0):.4f}")
        with row_cols[4]:
            st.write(f"${trade.get('price', 0):,.2f}")
        with row_cols[5]:
            st.write(f"${trade.get('fee', 0):.2f}")
    
    st.markdown("---")
    
    # Trade History Export
    export_col1, export_col2, export_col3 = st.columns([1, 1, 2])
    with export_col1:
        if st.button("📥 Export CSV", use_container_width=True):
            st.info("Export feature coming soon")
    with export_col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with export_col3:
        st.write()


if __name__ == "__main__":
    render_portfolio()
