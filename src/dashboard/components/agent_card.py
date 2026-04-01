"""
Dashboard Components - Agent Card
==================================
Reusable agent status card component.
"""

from __future__ import annotations

import streamlit as st
from typing import Dict, Any, Optional


def render_agent_card(
    agent: Dict[str, Any],
    key: Optional[str] = None,
    show_actions: bool = True,
) -> None:
    """
    Render a reusable agent status card.

    Args:
        agent: Dict with agent data (id, name, strategy, status, pnl, etc.)
        key: Optional Streamlit key for interactive elements
        show_actions: Whether to show action buttons
    """
    status_icons = {
        "running": "🟢",
        "paused": "🟡",
        "stopped": "🔴",
        "error": "🔴",
    }
    status_icon = status_icons.get(agent.get("status", "stopped"), "⚪")

    with st.container():
        # Header
        header_col1, header_col2 = st.columns([3, 1])
        with header_col1:
            st.markdown(f"### {status_icon} {agent.get('name', 'Unknown Agent')}")
            st.caption(f"`{agent.get('id', 'unknown')}` • {agent.get('strategy', 'N/A')}")
        with header_col2:
            status_color = {
                "running": "green",
                "paused": "yellow",
                "stopped": "red",
                "error": "red",
            }.get(agent.get("status", ""), "gray")
            st.markdown(
                f"<span style='color:{status_color};font-weight:bold;text-align:right;display:block'>"
                f"{agent.get('status', 'unknown').upper()}</span>",
                unsafe_allow_html=True,
            )

        # Metrics row
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            pnl = agent.get("pnl", 0)
            st.metric(
                "Total P&L",
                f"${pnl:,.2f}",
                delta_color="normal" if pnl >= 0 else "inverse",
            )
        with m_col2:
            st.metric("24h P&L", f"${agent.get('pnl_24h', 0):,.2f}")
        with m_col3:
            st.metric("Win Rate", f"{agent.get('win_rate', 0):.1f}%")
        with m_col4:
            st.metric("Trades", f"{agent.get('trades', 0):,}")

        # Secondary metrics
        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            st.caption(f"⏱️ Uptime: {agent.get('uptime', 'N/A')}")
        with s_col2:
            st.caption(f"🕐 Last Trade: {agent.get('last_trade', 'N/A')}")
        with s_col3:
            err = agent.get("errors", 0)
            err_color = "red" if err > 0 else "gray"
            st.markdown(f"<span style='color:{err_color}'>❌ Errors: {err}</span>", unsafe_allow_html=True)

        # Resource usage
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            st.progress(agent.get("memory_mb", 0) / 2048, text=f"Memory: {agent.get('memory_mb', 0)} MB")
        with r_col2:
            st.progress(agent.get("cpu_pct", 0) / 100, text=f"CPU: {agent.get('cpu_pct', 0):.1f}%")

        # Action buttons
        if show_actions:
            act_col1, act_col2, act_col3, act_col4 = st.columns(4)
            status = agent.get("status", "")
            with act_col1:
                if status == "running":
                    st.button("⏸️ Pause", key=f"{key}_pause" if key else None)
                else:
                    st.button("▶️ Start", key=f"{key}_start" if key else None)
            with act_col2:
                st.button("🔄 Restart", key=f"{key}_restart" if key else None)
            with act_col3:
                st.button("⚙️ Config", key=f"{key}_config" if key else None)
            with act_col4:
                st.button("🗑️ Remove", key=f"{key}_remove" if key else None)

        st.markdown("---")
