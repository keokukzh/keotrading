"""
KEOTrading Dashboard - Overview Page
====================================
System overview, total P&L, and agent status summary.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any


# Mock data for demonstration
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
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, -1, -1)]
    values = [1000 + i * 50 + (i % 3) * 100 + (i % 7) * -30 for i in range(31)]
    return pd.DataFrame({"date": dates, "pnl": values})


def get_mock_total_pnl() -> Dict[str, Any]:
    """Return mock total P&L summary."""
    return {
        "total": 12345.10,
        "daily": 432.50,
        "weekly": 2891.20,
        "monthly": 12345.10,
        "change_24h": 3.6,
    }


def render_overview() -> None:
    """Render the Overview page."""
    st.title("📊 System Overview")
    st.markdown("---")

    # Total P&L Section
    total_pnl = get_mock_total_pnl()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total P&L",
            value=f"${total_pnl['total']:,.2f}",
            delta=f"{total_pnl['change_24h']}% (24h)"
        )
    with col2:
        st.metric("Daily P&L", f"${total_pnl['daily']:,.2f}")
    with col3:
        st.metric("Weekly P&L", f"${total_pnl['weekly']:,.2f}")
    with col4:
        st.metric("Monthly P&L", f"${total_pnl['monthly']:,.2f}")

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
        portfolio_data = {
            "Asset": ["USDT", "BTC", "ETH", "SOL", "Other"],
            "Allocation": [45, 25, 15, 10, 5],
        }
        pie_fig = px.pie(
            portfolio_data,
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
            st.write(agent["strategy"])
        with col_status:
            status_icon = status_colors.get(agent["status"], "⚪")
            st.write(f"{status_icon} {agent['status'].capitalize()}")
        with col_pnl:
            pnl_color = "green" if agent["pnl"] >= 0 else "red"
            st.markdown(f"<span style='color:{pnl_color}'>${agent['pnl']:,.2f}</span>", unsafe_allow_html=True)
        with col_uptime:
            st.write(agent["uptime"])
        with col_actions:
            if agent["status"] == "running":
                if st.button(f"⏸️", key=f"pause_{agent['id']}"):
                    st.info(f"Pause action for {agent['name']} would be sent via API")
            else:
                if st.button(f"▶️", key=f"start_{agent['id']}"):
                    st.info(f"Start action for {agent['name']} would be sent via API")

    st.markdown("---")

    # System Health
    st.subheader("🩺 System Health")
    health_col1, health_col2, health_col3, health_col4 = st.columns(4)
    with health_col1:
        st.metric("CPU Usage", "34%", "-5%")
    with health_col2:
        st.metric("Memory", "2.4 GB", "+0.3 GB")
    with health_col3:
        st.metric("API Latency", "45ms", "-12ms")
    with health_col4:
        st.metric("Error Rate", "0.02%", "Stable")


if __name__ == "__main__":
    render_overview()
