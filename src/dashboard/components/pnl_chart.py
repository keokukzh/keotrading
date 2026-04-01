"""
Dashboard Components - P&L Chart
================================
P&L visualization using Plotly.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Optional, List, Dict, Any


def render_pnl_line_chart(
    df: pd.DataFrame,
    x_col: str = "date",
    y_col: str = "pnl",
    title: str = "P&L Over Time",
    height: int = 300,
    color: str = "#00D4AA",
    fill: bool = True,
) -> None:
    """
    Render a line chart for P&L data.

    Args:
        df: DataFrame with date and pnl columns
        x_col: Column name for x-axis (dates)
        y_col: Column name for y-axis (P&L values)
        title: Chart title
        height: Chart height in pixels
        color: Line color
        fill: Whether to fill area under line
    """
    fig = go.Figure()

    fill_color = f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)"

    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode="lines+markers",
        fill="tozeroy" if fill else "none",
        line=dict(color=color, width=2),
        fillcolor=fill_color,
        name=y_col,
        marker=dict(size=4, color=color),
    ))

    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=14)),
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, ticks=""),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            tickprefix="$",
        ),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_pnl_bar_chart(
    df: pd.DataFrame,
    x_col: str = "date",
    y_col: str = "pnl",
    title: str = "Daily P&L",
    height: int = 250,
) -> None:
    """
    Render a bar chart for daily P&L.

    Args:
        df: DataFrame with date and pnl columns
        x_col: Column name for x-axis
        y_col: Column name for y-axis (values)
        title: Chart title
        height: Chart height in pixels
    """
    colors = ["#00D4AA" if v >= 0 else "#FF6B6B" for v in df[y_col]]

    fig = go.Figure(go.Bar(
        x=df[x_col],
        y=df[y_col],
        marker_color=colors,
        name=y_col,
    ))

    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=14)),
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, ticks=""),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            tickprefix="$",
        ),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_cumulative_pnl_chart(
    df: pd.DataFrame,
    x_col: str = "date",
    y_col: str = "pnl_cumulative",
    title: str = "Cumulative P&L",
    height: int = 300,
) -> None:
    """
    Render a cumulative P&L area chart.

    Args:
        df: DataFrame with date and cumulative pnl
        x_col: Column name for x-axis
        y_col: Column name for cumulative values
        title: Chart title
        height: Chart height in pixels
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode="lines",
        fill="tozeroy",
        line=dict(color="#4ECDC4", width=2),
        fillcolor="rgba(78, 205, 196, 0.1)",
        name="Cumulative P&L",
    ))

    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=14)),
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, ticks=""),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            tickprefix="$",
        ),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)
