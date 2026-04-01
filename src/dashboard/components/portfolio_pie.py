"""
Dashboard Components - Portfolio Pie Chart
==========================================
Portfolio allocation visualization using Plotly.
"""

from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional


DEFAULT_COLORS = [
    "#00D4AA",  # teal
    "#FF6B6B",  # coral red
    "#4ECDC4",  # turquoise
    "#FFD93D",  # yellow
    "#95A5A6",  # gray
    "#7B68EE",  # medium purple
    "#20B2AA",  # light sea green
    "#DDA0DD",  # plum
    "#F0E68C",  # khaki
    "#87CEEB",  # sky blue
]


def render_portfolio_pie(
    positions: List[Dict[str, Any]],
    value_col: str = "value_usd",
    label_col: str = "asset",
    title: str = "Portfolio Allocation",
    height: int = 350,
    hole: float = 0.5,
    colors: Optional[List[str]] = None,
) -> None:
    """
    Render a donut chart for portfolio allocation.

    Args:
        positions: List of position dicts with value and label columns
        value_col: Column name for values
        label_col: Column name for labels
        title: Chart title
        height: Chart height in pixels
        hole: Hole size (0 = pie, 0.5+ = donut)
        colors: Optional custom color list
    """
    data = {
        label_col: [p[label_col] for p in positions],
        value_col: [p[value_col] for p in positions],
    }

    color_seq = colors or DEFAULT_COLORS

    fig = px.pie(
        data,
        values=value_col,
        names=label_col,
        hole=hole,
        color_discrete_sequence=color_seq,
    )

    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=14)),
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
    )

    # Add percentage labels
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_portfolio_bar(
    positions: List[Dict[str, Any]],
    value_col: str = "value_usd",
    label_col: str = "asset",
    title: str = "Portfolio Value by Asset",
    height: int = 300,
    colors: Optional[List[str]] = None,
) -> None:
    """
    Render a horizontal bar chart for portfolio allocation.

    Args:
        positions: List of position dicts
        value_col: Column name for values
        label_col: Column name for labels
        title: Chart title
        height: Chart height in pixels
        colors: Optional custom color list
    """
    data = {
        label_col: [p[label_col] for p in positions],
        value_col: [p[value_col] for p in positions],
    }

    color_seq = colors or DEFAULT_COLORS[:len(positions)]

    fig = px.bar(
        data,
        x=value_col,
        y=label_col,
        orientation="h",
        color=label_col,
        color_discrete_sequence=color_seq,
    )

    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=14)),
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            tickprefix="$",
        ),
        yaxis=dict(showgrid=False),
    )

    # Add value labels on bars
    fig.update_traces(
        texttemplate="$%{x:,.0f}",
        textposition="outside",
        hovertemplate="%{y}: $%{x:,.0f}",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_allocation_table(
    positions: List[Dict[str, Any]],
    value_col: str = "value_usd",
    label_col: str = "asset",
    allocation_col: str = "allocation",
    source_col: str = "source",
) -> None:
    """
    Render a styled allocation table.

    Args:
        positions: List of position dicts
        value_col: Column name for values
        label_col: Column name for asset labels
        allocation_col: Column name for allocation percentages
        source_col: Column name for source
    """
    rows = []
    for p in positions:
        rows.append({
            "Asset": p.get(label_col, "Unknown"),
            "Value (USD)": f"${p.get(value_col, 0):,.2f}",
            "Allocation": f"{p.get(allocation_col, 0)*100:.1f}%",
            "Source": p.get(source_col, "N/A"),
        })

    # Progress bars for allocation
    for row in rows:
        alloc_pct = float(row["Allocation"].replace("%", ""))
        st.progress(alloc_pct / 100, text=f"{row['Asset']}: {row['Allocation']} ({row['Value (USD)']})")
