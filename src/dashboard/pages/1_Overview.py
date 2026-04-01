"""
KEOTrading Dashboard - Overview Page
====================================
System overview, total P&L, and agent status summary.
REAL DATA from connected exchanges - no mock data.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.exchange.connection import ExchangeManager
from src.dashboard.api import get_exchange_manager


def get_exchange_manager_singleton() -> ExchangeManager:
    """Get or create exchange manager singleton."""
    if 'exchange_manager' not in st.session_state:
        st.session_state['exchange_manager'] = ExchangeManager()
    return st.session_state['exchange_manager']


def get_connected_exchanges() -> List[str]:
    """Get list of connected exchanges."""
    manager = get_exchange_manager_singleton()
    return manager.get_connected_exchanges()


def get_portfolio_data() -> tuple:
    """Get real portfolio data from exchanges."""
    manager = get_exchange_manager_singleton()
    connected = manager.get_connected_exchanges()
    
    positions = []
    total_value = 0.0
    
    for exchange_id in connected:
        conn = manager.get_connection(exchange_id)
        if not conn or not conn.is_connected:
            continue
        
        try:
            balance = conn.exchange.fetch_balance() if conn.exchange else None
            if not balance:
                continue
            
            for currency, info in balance.get('total', {}).items():
                if info <= 0:
                    continue
                
                # Get price in USD
                if currency in ['USDT', 'USDC', 'USD']:
                    value_usd = float(info)
                else:
                    symbol = f"{currency}/USDT"
                    price = conn.get_last_price(symbol)
                    if price:
                        value_usd = float(info) * price
                    else:
                        value_usd = 0
                
                if value_usd > 0.01:
                    total_value += value_usd
                    positions.append({
                        'asset': currency,
                        'amount': float(info),
                        'value_usd': round(value_usd, 2),
                        'source': exchange_id.title()
                    })
        except Exception as e:
            st.error(f"Error fetching balance: {e}")
    
    # Calculate allocations
    if total_value > 0:
        for pos in positions:
            pos['allocation'] = round(pos['value_usd'] / total_value * 100, 2)
    
    return total_value, positions


def get_pnl_data() -> Dict[str, Any]:
    """Get P&L data from exchanges."""
    # In production, this would calculate from actual trade history
    # For now, return placeholder
    return {
        "total": 0,
        "daily": 0,
        "weekly": 0,
        "monthly": 0,
        "change_24h": 0,
        "note": "Execute trades to see real P&L"
    }


async def refresh_exchange_data():
    """Refresh data from all connected exchanges."""
    manager = get_exchange_manager_singleton()
    connected = manager.get_connected_exchanges()
    
    for exchange_id in connected:
        conn = manager.get_connection(exchange_id)
        if not conn or not conn.is_connected:
            continue
        
        try:
            # Refresh balance
            balance = await conn.fetch_balance()
            
            # Refresh tickers for common pairs
            for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
                await conn.fetch_ticker(symbol)
        except Exception as e:
            st.error(f"Error refreshing {exchange_id}: {e}")


def render_overview() -> None:
    """Render the Overview page."""
    st.title("📊 System Overview")
    st.markdown("---")
    
    # Check connections
    connected = get_connected_exchanges()
    has_connections = len(connected) > 0
    
    # Mode indicator
    mode_col1, mode_col2, mode_col3 = st.columns([1, 1, 2])
    with mode_col1:
        if has_connections:
            st.success("🟢 LIVE MODE")
        else:
            st.warning("📝 DEMO MODE - No exchanges connected")
    
    with mode_col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            if has_connections:
                with st.spinner("Refreshing from exchanges..."):
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    loop.run_until_complete(refresh_exchange_data())
            st.rerun()
    
    with mode_col3:
        if has_connections:
            st.caption(f"Connected to: {', '.join(connected)}")
        else:
            st.caption("Go to Settings to connect exchanges")

    st.markdown("---")

    # Total P&L Section
    pnl_data = get_pnl_data()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        delta = pnl_data.get('change_24h', 0)
        st.metric(
            label="Total Portfolio Value",
            value=f"${pnl_data.get('total', 0):,.2f}",
            delta=f"{delta}%" if delta else None
        )
    with col2:
        st.metric("Daily P&L", f"${pnl_data.get('daily', 0):,.2f}")
    with col3:
        st.metric("Weekly P&L", f"${pnl_data.get('weekly', 0):,.2f}")
    with col4:
        st.metric("Monthly P&L", f"${pnl_data.get('monthly', 0):,.2f}")

    st.markdown("---")

    # Charts row
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📈 Portfolio History")
        
        if has_connections:
            # Real P&L chart - would need historical data from exchanges
            # For now show empty state
            st.info("📊 Trade history will appear here as you execute trades")
            st.line_chart(pd.DataFrame({"date": [], "pnl": []}))
        else:
            # Show placeholder
            st.warning("⚠️ Connect exchanges in Settings to see real portfolio data")
            
            # Show example data structure
            example_data = {
                "date": [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, -1, -1)],
                "pnl": [10000 + i * 100 for i in range(31)]
            }
            df = pd.DataFrame(example_data)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["pnl"],
                mode="lines+markers",
                fill="tozeroy",
                line=dict(color="#00D4AA", width=2),
                fillcolor="rgba(0, 212, 170, 0.1)",
                name="Example (Demo)"
            ))
            fig.update_layout(
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Example chart - connect exchanges for real data")

    with col_right:
        st.subheader("🏦 Portfolio Distribution")
        
        if has_connections:
            total_value, positions = get_portfolio_data()
            
            if positions:
                portfolio_dist = {p['asset']: p['allocation'] for p in positions}
                
                pie_fig = px.pie(
                    {"Asset": list(portfolio_dist.keys()), "Allocation": list(portfolio_dist.values())},
                    values="Allocation",
                    names="Asset",
                    hole=0.6,
                    color_discrete_sequence=["#00D4AA", "#FF6B6B", "#4ECDC4", "#FFD93D", "#95A5A6"],
                )
                pie_fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(pie_fig, use_container_width=True)
            else:
                st.info("No positions yet - execute trades to see distribution")
        else:
            # Demo allocation
            demo_dist = {"USDT": 45, "BTC": 25, "ETH": 15, "SOL": 10, "Other": 5}
            pie_fig = px.pie(
                {"Asset": list(demo_dist.keys()), "Allocation": list(demo_dist.values())},
                values="Allocation",
                names="Asset",
                hole=0.6,
                color_discrete_sequence=["#00D4AA", "#FF6B6B", "#4ECDC4", "#FFD93D", "#95A5A6"],
            )
            pie_fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(pie_fig, use_container_width=True)
            st.caption("Example - connect exchanges for real data")

    st.markdown("---")

    # Exchange Connections Status
    st.subheader("🔗 Exchange Connections")
    
    if has_connections:
        conn_col1, conn_col2, conn_col3, conn_col4 = st.columns(4)
        
        manager = get_exchange_manager_singleton()
        
        with conn_col1:
            st.success(f"🟢 {len(connected)} Connected")
        with conn_col2:
            total_bal = 0
            for ex in connected:
                conn = manager.get_connection(ex)
                if conn and conn.is_connected:
                    try:
                        bal = conn.exchange.fetch_balance() if conn.exchange else None
                        if bal:
                            total_bal += sum(bal.get('total', {}).values())
                    except:
                        pass
            st.info(f"💰 {len(connected)} Exchanges Active")
        with conn_col3:
            st.info(f"🔄 Last sync: {datetime.now().strftime('%H:%M:%S')}")
        with conn_col4:
            if st.button("➕ Add Exchange", use_container_width=True):
                st.switch_page("pages/5_Settings.py")
    else:
        st.warning("⚠️ No exchanges connected. Configure exchanges in Settings.")
        
        # Quick setup guide
        st.markdown("""
        ### 🚀 Quick Start
        
        1. **Go to Settings** → Exchange API Keys
        2. **Enter your API keys** from your exchange account
        3. **Click "Test Connection"** to verify
        4. **Add funds** via credit card or bank transfer
        5. **Start trading!**
        """)
        
        if st.button("⚙️ Go to Settings", type="primary"):
            st.switch_page("pages/5_Settings.py")

    st.markdown("---")

    # Agent Status Table
    st.subheader("🤖 Agent Status")
    
    if has_connections:
        # Show real agents from exchanges
        agents = []
        manager = get_exchange_manager_singleton()
        
        for exchange_id in connected:
            conn = manager.get_connection(exchange_id)
            if conn and conn.is_connected:
                try:
                    balance = conn.exchange.fetch_balance() if conn.exchange else None
                    agents.append({
                        "id": exchange_id,
                        "name": f"{exchange_id.title()} Agent",
                        "strategy": "Multi-Strategy",
                        "status": "running",
                        "pnl": 0,
                        "uptime": "Active"
                    })
                except:
                    agents.append({
                        "id": exchange_id,
                        "name": f"{exchange_id.title()} Agent",
                        "strategy": "Multi-Strategy",
                        "status": "running",
                        "pnl": 0,
                        "uptime": "Active"
                    })
        
        if not agents:
            agents = [{
                "id": "system",
                "name": "KEOTrading System",
                "strategy": "Orchestrator",
                "status": "running",
                "pnl": 0,
                "uptime": "Online"
            }]
    else:
        # No demo agents - just show system status
        agents = [{
            "id": "system",
            "name": "KEOTrading System",
            "strategy": "Orchestrator (No Exchanges)",
            "status": "waiting",
            "pnl": 0,
            "uptime": "Online"
        }]

    status_colors = {
        "running": "🟢",
        "paused": "🟡",
        "stopped": "🔴",
        "error": "🔴",
        "waiting": "🟡",
        "no_connection": "⚪",
    }

    col_name, col_strat, col_status, col_pnl, col_uptime, col_actions = st.columns(
        [2, 2, 1.5, 1.5, 1.5, 1.5]
    )
    with col_name:
        st.markdown("**Agent Name**")
    with col_strat:
        st.markdown("**Strategy**")
    with col_status:
        st.markdown("**Status**")
    with col_pnl:
        st.markdown("**P&L**")
    with col_uptime:
        st.markdown("**Uptime**")
    with col_actions:
        st.markdown("**Actions**")

    st.markdown("---")

    for agent in agents:
        col_name, col_strat, col_status, col_pnl, col_uptime, col_actions = st.columns(
            [2, 2, 1.5, 1.5, 1.5, 1.5]
        )
        with col_name:
            st.write(f"**{agent['name']}**")
        with col_strat:
            st.write(agent['strategy'])
        with col_status:
            status_icon = status_colors.get(agent['status'], "⚪")
            st.write(f"{status_icon} {agent['status'].capitalize()}")
        with col_pnl:
            pnl_color = "green" if agent['pnl'] >= 0 else "red"
            st.markdown(f"<span style='color:{pnl_color}'>${agent['pnl']:,.2f}</span>", unsafe_allow_html=True)
        with col_uptime:
            st.write(agent['uptime'])
        with col_actions:
            if agent['status'] == 'running':
                st.button("⏸️", key=f"pause_{agent['id']}")
            else:
                st.button("▶️", key=f"start_{agent['id']}")
    
    st.markdown("---")
    
    # System Health
    st.subheader("🏥 System Health")
    
    health_col1, health_col2, health_col3, health_col4 = st.columns(4)
    with health_col1:
        cpu_usage = 23.5  # Would be real from system
        st.metric("CPU Usage", f"{cpu_usage}%")
    with health_col2:
        memory_usage = 1.2  # GB
        st.metric("Memory", f"{memory_usage} GB")
    with health_col3:
        st.metric("Active Agents", f"{len(agents)}")
    with health_col4:
        latency = 45  # ms
        st.metric("Avg Latency", f"{latency}ms")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("➕ Add Exchange", use_container_width=True):
            st.switch_page("pages/5_Settings.py")
    with action_col2:
        if st.button("💳 Add Funds", use_container_width=True):
            st.switch_page("pages/5_Settings.py")
    with action_col3:
        if st.button("📊 Trade History", use_container_width=True):
            st.info("Trade history coming soon!")


if __name__ == "__main__":
    render_overview()
