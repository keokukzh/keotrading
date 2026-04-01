"""
KEOTrading Dashboard - Portfolio Page
=====================================
Portfolio management, allocation, and position tracking.
"""

from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any


def get_mock_positions() -> List[Dict[str, Any]]:
    """Return mock position data."""
    return [
        {"asset": "USDT", "amount": 45000.00, "value_usd": 45000.00, "allocation": 0.45, "source": "Binance"},
        {"asset": "BTC", "amount": 0.85, "value_usd": 25000.00, "allocation": 0.25, "source": "CEX"},
        {"asset": "ETH", "amount": 8.5, "value_usd": 15000.00, "allocation": 0.15, "source": "CEX"},
        {"asset": "SOL", "amount": 75.0, "value_usd": 10000.00, "allocation": 0.10, "source": "Solana DEX"},
        {"asset": "RAY", "amount": 500.0, "value_usd": 1500.00, "allocation": 0.015, "source": "Raydium LP"},
        {"asset": "SRM", "amount": 200.0, "value_usd": 500.00, "allocation": 0.005, "source": "Solana DEX"},
        {"asset": "ORCA", "amount": 300.0, "value_usd": 1000.00, "allocation": 0.01, "source": "Orca LP"},
        {"asset": "Other", "amount": 1.0, "value_usd": 1000.00, "allocation": 0.01, "source": "Various"},
    ]


def get_mock_history() -> pd.DataFrame:
    """Return mock portfolio history."""
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, -1, -1)]
    values = []
    running = 80000
    for i in range(31):
        change = (i % 3 - 1) * 500 + (i % 7) * 200
        running += change
        values.append(running)
    return pd.DataFrame({"date": dates, "value": values})


def render_portfolio() -> None:
    """Render the Portfolio page."""
    st.title("💼 Portfolio Management")
    st.markdown("Track your portfolio allocation, positions, and performance.")
    st.markdown("---")

    positions = get_mock_positions()
    history = get_mock_history()
    total_value = sum(p["value_usd"] for p in positions)

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Value", f"${total_value:,.2f}")
    with col2:
        st.metric("Assets", f"{len(positions)}")
    with col3:
        st.metric("24h Change", "+$432.50", "+0.54%")
    with col4:
        st.metric("7d Change", "+$2,891.20", "+3.74%")

    st.markdown("---")

    # Charts
    chart_col1, chart_col2 = st.columns([1, 1])

    with chart_col1:
        st.subheader("📊 Portfolio History (30d)")
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
            "asset": [p["asset"] for p in positions],
            "value": [p["value_usd"] for p in positions],
        }
        pie_fig = px.pie(
            pie_data,
            values="value",
            names="asset",
            hole=0.5,
            color_discrete_sequence=["#00D4AA", "#FF6B6B", "#4ECDC4", "#FFD93D", "#95A5A6", "#7B68EE", "#20B2AA", "#DDA0DD"],
        )
        pie_fig.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(pie_fig, use_container_width=True)

    st.markdown("---")

    # Positions table
    st.subheader("📋 Open Positions")
    col_id, col_asset, col_amount, col_value, col_alloc, col_source, col_action = st.columns(
        [0.5, 1, 1.5, 1.5, 1, 1.5, 1]
    )
    with col_id:
        st.markdown("**#**")
    with col_asset:
        st.markdown("**Asset**")
    with col_amount:
        st.markdown("**Amount**")
    with col_value:
        st.markdown("**Value (USD)**")
    with col_alloc:
        st.markdown("**Allocation**")
    with col_source:
        st.markdown("**Source**")
    with col_action:
        st.markdown("**Action**")

    st.markdown("---")

    for idx, pos in enumerate(positions, 1):
        col_id, col_asset, col_amount, col_value, col_alloc, col_source, col_action = st.columns(
            [0.5, 1, 1.5, 1.5, 1, 1.5, 1]
        )
        with col_id:
            st.write(f"`{idx}`")
        with col_asset:
            st.write(f"**{pos['asset']}**")
        with col_amount:
            if isinstance(pos['amount'], float) and pos['amount'] < 100:
                st.write(f"{pos['amount']:.4f}")
            else:
                st.write(f"{pos['amount']:,.2f}")
        with col_value:
            st.write(f"${pos['value_usd']:,.2f}")
        with col_alloc:
            st.write(f"{pos['allocation']*100:.1f}%")
        with col_source:
            st.write(pos['source'])
        with col_action:
            st.button("Trade", key=f"trade_{pos['asset']}")

    st.markdown("---")

    # Rebalance panel
    st.subheader("⚖️ Portfolio Rebalancing")
    st.markdown(
        "Rebalancing helps maintain your target allocation. "
        "Current drift from targets is shown below."
    )

    target_col1, target_col2, target_col3 = st.columns(3)
    with target_col1:
        st.selectbox("Target Strategy", options=["Conservative", "Balanced", "Aggressive"])
    with target_col2:
        st.selectbox("Rebalance Trigger", options=["Daily", "Weekly", "Threshold (5%)", "Manual"])
    with target_col3:
        st.button("🔄 Rebalance Now")

    # Drift analysis
    st.markdown("#### Drift Analysis")
    drift_data = []
    for pos in positions:
        drift = (pos["allocation"] - (1/len(positions))) * 100
        drift_data.append({
            "Asset": pos["asset"],
            "Current": f"{pos['allocation']*100:.1f}%",
            "Target": f"{100/len(positions):.1f}%",
            "Drift": f"{drift:+.1f}%",
        })

    drift_df = pd.DataFrame(drift_data)
    st.dataframe(drift_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render_portfolio()
