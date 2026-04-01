"""
KEOTrading Dashboard - Agents Page
===================================
Individual agent monitoring with detailed stats and controls.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional


def get_detailed_agent_data() -> List[Dict[str, Any]]:
    """Return detailed agent data."""
    return [
        {
            "id": "agent-001",
            "name": "Hzjken LP Agent",
            "strategy": "LP Arbitrage",
            "status": "running",
            "pnl_total": 4521.30,
            "pnl_24h": 234.50,
            "pnl_7d": 1203.80,
            "trades": 1247,
            "win_rate": 72.4,
            "avg_trade": 3.62,
            "uptime": "6d 14h 22m",
            "last_trade": "2 min ago",
            "memory_mb": 512,
            "cpu_pct": 12.5,
            "errors": 0,
        },
        {
            "id": "agent-002",
            "name": "Scalper Alpha",
            "strategy": "Scalping",
            "status": "running",
            "pnl_total": 2134.80,
            "pnl_24h": 87.20,
            "pnl_7d": 456.30,
            "trades": 3421,
            "win_rate": 61.8,
            "avg_trade": 0.62,
            "uptime": "3d 2h 15m",
            "last_trade": "30 sec ago",
            "memory_mb": 384,
            "cpu_pct": 18.3,
            "errors": 2,
        },
        {
            "id": "agent-003",
            "name": "Grid Bot Beta",
            "strategy": "Grid Trading",
            "status": "paused",
            "pnl_total": -234.50,
            "pnl_24h": -12.30,
            "pnl_7d": 89.40,
            "trades": 156,
            "win_rate": 54.2,
            "avg_trade": -1.50,
            "uptime": "2d 8h 05m",
            "last_trade": "4h ago",
            "memory_mb": 256,
            "cpu_pct": 3.2,
            "errors": 5,
        },
        {
            "id": "agent-004",
            "name": "Momentum Hunter",
            "strategy": "Momentum",
            "status": "running",
            "pnl_total": 1876.20,
            "pnl_24h": 156.80,
            "pnl_7d": 523.10,
            "trades": 89,
            "win_rate": 48.3,
            "avg_trade": 21.08,
            "uptime": "1d 5h 33m",
            "last_trade": "12 min ago",
            "memory_mb": 768,
            "cpu_pct": 22.1,
            "errors": 0,
        },
        {
            "id": "agent-005",
            "name": "DEX Scout",
            "strategy": "DEX Arbitrage",
            "status": "running",
            "pnl_total": 3214.90,
            "pnl_24h": 198.40,
            "pnl_7d": 812.60,
            "trades": 2156,
            "win_rate": 68.9,
            "avg_trade": 1.49,
            "uptime": "4d 18h 47m",
            "last_trade": "1 min ago",
            "memory_mb": 640,
            "cpu_pct": 15.7,
            "errors": 1,
        },
        {
            "id": "agent-006",
            "name": "LLM Advisor",
            "strategy": "LLM Enhanced",
            "status": "running",
            "pnl_total": 892.40,
            "pnl_24h": 45.60,
            "pnl_7d": 234.80,
            "trades": 67,
            "win_rate": 59.7,
            "avg_trade": 13.32,
            "uptime": "5d 0h 12m",
            "last_trade": "8 min ago",
            "memory_mb": 1024,
            "cpu_pct": 28.4,
            "errors": 0,
        },
    ]


def render_agent_detail(agent: Dict[str, Any]) -> None:
    """Render detailed view for a single agent."""
    status_emoji = {"running": "🟢", "paused": "🟡", "stopped": "🔴", "error": "🔴"}

    st.markdown(f"#### {status_emoji.get(agent['status'], '⚪')} {agent['name']} (`{agent['id']}`)")
    st.markdown(f"**Strategy:** {agent['strategy']} | **Status:** {agent['status'].capitalize()}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total P&L", f"${agent['pnl_total']:,.2f}")
    with col2:
        st.metric("24h P&L", f"${agent['pnl_24h']:,.2f}")
    with col3:
        st.metric("7d P&L", f"${agent['pnl_7d']:,.2f}")
    with col4:
        st.metric("Win Rate", f"{agent['win_rate']}%")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Total Trades", f"{agent['trades']:,}")
    with col6:
        st.metric("Avg Trade", f"${agent['avg_trade']:.2f}")
    with col7:
        st.metric("Uptime", agent['uptime'])
    with col8:
        st.metric("Last Trade", agent['last_trade'])

    col9, col10, col11 = st.columns(3)
    with col9:
        st.metric("Memory", f"{agent['memory_mb']} MB")
    with col10:
        st.metric("CPU", f"{agent['cpu_pct']}%")
    with col11:
        st.metric("Errors", f"{agent['errors']}")

    # Mini P&L chart for this agent
    import random
    dates = pd.date_range(end=datetime.now(), periods=14, freq="D")
    pnl_values = [random.uniform(-50, 100) for _ in range(14)]
    cumulative = []
    running = 0
    for v in pnl_values:
        running += v
        cumulative.append(running)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=cumulative,
        mode="lines",
        line=dict(color="#00D4AA", width=2),
        name="Cumulative P&L"
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(showgrid=False, ticks="", showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Action buttons
    act_col1, act_col2, act_col3, act_col4 = st.columns(4)
    with act_col1:
        if agent["status"] == "running":
            st.button("⏸️ Pause", key=f"pause_detail_{agent['id']}")
        else:
            st.button("▶️ Resume", key=f"resume_detail_{agent['id']}")
    with act_col2:
        st.button("🔄 Restart", key=f"restart_{agent['id']}")
    with act_col3:
        st.button("⚙️ Configure", key=f"config_{agent['id']}")
    with act_col4:
        st.button("🗑️ Stop & Remove", key=f"remove_{agent['id']}")

    st.markdown("---")


def render_agents() -> None:
    """Render the Agents monitoring page."""
    st.title("🤖 Agent Monitoring")
    st.markdown("Detailed view and control for each trading agent.")
    st.markdown("---")

    agents = get_detailed_agent_data()

    # Filter by status
    st.subheader("Filter")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        status_filter = st.multiselect(
            "Status",
            options=["running", "paused", "stopped", "error"],
            default=["running", "paused"],
        )
    with filter_col2:
        strategy_filter = st.multiselect(
            "Strategy",
            options=list(set(a["strategy"] for a in agents)),
            default=list(set(a["strategy"] for a in agents)),
        )
    with filter_col3:
        sort_by = st.selectbox(
            "Sort by",
            options=["pnl_total", "pnl_24h", "win_rate", "trades"],
            format_func=lambda x: {
                "pnl_total": "Total P&L",
                "pnl_24h": "24h P&L",
                "win_rate": "Win Rate",
                "trades": "Trade Count",
            }[x],
        )

    # Apply filters
    filtered = [
        a for a in agents
        if a["status"] in status_filter and a["strategy"] in strategy_filter
    ]
    filtered.sort(key=lambda x: x[sort_by], reverse=True)

    st.markdown(f"Showing {len(filtered)} of {len(agents)} agents")
    st.markdown("---")

    # Summary metrics
    total_pnl = sum(a["pnl_total"] for a in filtered)
    total_24h = sum(a["pnl_24h"] for a in filtered)
    avg_win_rate = sum(a["win_rate"] for a in filtered) / len(filtered) if filtered else 0

    sum_col1, sum_col2, sum_col3 = st.columns(3)
    with sum_col1:
        st.metric("Combined P&L", f"${total_pnl:,.2f}")
    with sum_col2:
        st.metric("Combined 24h P&L", f"${total_24h:,.2f}")
    with sum_col3:
        st.metric("Avg Win Rate", f"{avg_win_rate:.1f}%")

    st.markdown("---")

    # Individual agent cards
    for agent in filtered:
        render_agent_detail(agent)


if __name__ == "__main__":
    render_agents()
