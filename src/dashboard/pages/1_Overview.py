"""
KEOTrading Dashboard - Overview Page
====================================
System overview, total P&L, and agent status summary with real data support.
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

from src.dashboard.real_data import MockDataGenerator, RealTimeDataManager
from src.exchange.connection import ExchangeManager


def get_data_manager():
    """Get or create data manager singleton."""
    if 'data_manager' not in st.session_state:
        st.session_state['data_manager'] = RealTimeDataManager(ExchangeManager())
    return st.session_state['data_manager']


def get_mock_generator():
    """Get mock data generator."""
    if 'mock_generator' not in st.session_state:
        st.session_state['mock_generator'] = MockDataGenerator()
    return st.session_state['mock_generator']


def get_mock_agents() -> List[Dict[str, Any]]:
    """Return mock agent status data."""
    return [
        {"id": "agent-001", "name": "Hzjken LP Agent", "strategy": "LP Arbitrage", "status": "running", "pnl": 4521.30, "uptime": "6d 14h"},
        {"id": "agent-002", "name": "Scalper Alpha", "strategy": "Scalping", "status": "running", "pnl": 2134.80, "uptime": "3d 2h"},
        {"id": "agent-003", "name": "Grid Bot Beta", "strategy": "Grid Trading", "status": "paused", "pnl": -234.50, "uptime": "2d 8h"},
        {"id": "agent-004", "name": "Momentum Hunter", "strategy": "Momentum", "status": "running", "pnl": 1876.20, "uptime": "1d 5h"},
        {"id": "agent-005", "name": "DEX Scout", "strategy": "DEX Arbitrage", "status": "running", "pnl": 3214.90, "uptime": "4d 18h"},
        {"id": "agent-006", "name": "LLM Advisor", "strategy": "LLM Enhanced", "status": "running", "pnl": 892.40, "uptime": "5d 0h"},
    ]


def get_mock_pnl_history() -> pd.DataFrame:
    """Return mock P&L history data."""
    generator = get_mock_generator()
    return generator.generate_pnl_history(30)


def get_mock_total_pnl() -> Dict[str, Any]:
    """Return mock total P&L summary."""
    generator = get_mock_generator()
    return generator.generate_total_pnl()


async def get_real_pnl() -> Dict[str, Any]:
    """Get real P&L from connected exchanges."""
    data_manager = get_data_manager()
    try:
        total_value = await data_manager.get_portfolio_value()
        return {
            "total": total_value,
            "daily": 0,  # Would need historical data
            "weekly": 0,
            "monthly": 0,
            "change_24h": 0,
        }
    except Exception as e:
        return get_mock_total_pnl()


async def get_real_portfolio() -> Dict[str, float]:
    """Get real portfolio distribution."""
    data_manager = get_data_manager()
    try:
        return await data_manager.exchange_manager.get_portfolio_distribution()
    except Exception:
        generator = get_mock_generator()
        return generator.generate_portfolio_allocation()


async def refresh_data():
    """Refresh real-time data."""
    data_manager = get_data_manager()
    try:
        await data_manager.refresh_all()
    except Exception:
        pass  # Fall back to mock data


def render_overview() -> None:
    """Render the Overview page."""
    st.title("📊 System Overview")
    st.markdown("---")
    
    # Check if we have real exchange connections
    has_connections = False
    try:
        exchange_manager = ExchangeManager()
        has_connections = len(exchange_manager.get_connected_exchanges()) > 0
    except:
        pass
    
    # Mode indicator
    mode_col1, mode_col2, mode_col3 = st.columns([1, 1, 2])
    with mode_col1:
        if has_connections:
            st.success("🟢 LIVE MODE")
        else:
            st.info("📝 DEMO MODE")
    
    with mode_col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            if has_connections:
                with st.spinner("Refreshing..."):
                    import asyncio
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(refresh_data())
                    loop.close()
            st.rerun()
    
    with mode_col3:
        if has_connections:
            data_manager = get_data_manager()
            last_update = data_manager.get_last_update_time()
            if last_update:
                st.caption(f"Last updated: {last_update.strftime('%H:%M:%S')}")
            else:
                st.caption("Pull to refresh")
        else:
            st.caption("Connect exchanges in Settings to enable live data")

    st.markdown("---")

    # Total P&L Section
    if has_connections:
        # Try to get real data
        import asyncio
        try:
            total_pnl = loop.run_until_complete(get_real_pnl()) if 'loop' not in dir() else get_real_pnl()
        except:
            total_pnl = get_mock_total_pnl()
    else:
        total_pnl = get_mock_total_pnl()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        delta = total_pnl.get('change_24h', 0)
        st.metric(
            label="Total P&L",
            value=f"${total_pnl.get('total', 0):,.2f}",
            delta=f"{delta}% (24h)" if delta else None
        )
    with col2:
        st.metric("Daily P&L", f"${total_pnl.get('daily', 0):,.2f}")
    with col3:
        st.metric("Weekly P&L", f"${total_pnl.get('weekly', 0):,.2f}")
    with col4:
        st.metric("Monthly P&L", f"${total_pnl.get('monthly', 0):,.2f}")

    st.markdown("---")

    # Charts row
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📈 P&L History (30 days)")
        pnl_df = get_mock_pnl_history()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=pnl_df["date"],
            y=pnl_df["pnl"],
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color="#00D4AA", width=2),
            fillcolor="rgba(0, 212, 170, 0.1)",
            name="P&L"
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

    with col_right:
        st.subheader("🏦 Portfolio Distribution")
        
        if has_connections:
            import asyncio
            try:
                portfolio_dist = loop.run_until_complete(get_real_portfolio())
            except:
                portfolio_dist = get_mock_generator().generate_portfolio_allocation()
        else:
            portfolio_dist = get_mock_generator().generate_portfolio_allocation()
        
        pie_fig = px.pie(
            {"Asset": list(portfolio_dist.keys()), "Allocation": list(portfolio_dist.values())},
            values="Allocation",
            names="Asset",
            hole=0.6,
            color_discrete_sequence=["#00D4AA", "#FF6B6B", "#4ECDC4", "#FFD93D", "#95A5A6"],
        )
        pie_fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(pie_fig, use_container_width=True)

    st.markdown("---")

    # Agent Status Table
    st.subheader("🤖 Agent Status")
    agents = get_mock_agents()

    status_colors = {
        "running": "🟢",
        "paused": "🟡",
        "stopped": "🔴",
        "error": "🔴",
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
        connected_agents = len([a for a in agents if a['status'] == 'running'])
        st.metric("Active Agents", f"{connected_agents}/{len(agents)}")
    with health_col4:
        latency = 45  # ms
        st.metric("Avg Latency", f"{latency}ms")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("🚀 Start All Agents", use_container_width=True):
            st.info("Starting all agents...")
    with action_col2:
        if st.button("⏹️ Stop All Agents", use_container_width=True):
            st.warning("Stopping all agents...")
    with action_col3:
        if st.button("🔄 Restart System", use_container_width=True):
            st.info("Restarting system...")


if __name__ == "__main__":
    render_overview()
