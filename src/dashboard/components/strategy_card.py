"""
Dashboard Components - Strategy Card
======================================
Strategy selection card component.
"""

from __future__ import annotations

import streamlit as st
from typing import Dict, Any, Optional, Callable


def render_stars(n: int) -> str:
    """Render star rating as emoji string."""
    return "⭐" * n


def render_risk_badge(risk: str) -> str:
    """Render risk level as emoji badge."""
    risk_map = {
        "Low": "🟢 Low",
        "Low-Medium": "🟢🟡 Low-Medium",
        "Medium": "🟡 Medium",
        "Medium-High": "🟡🟠 Medium-High",
        "High": "🟠 High",
        "Medium (adaptive)": "🟡🤖 Medium (adaptive)",
        "Medium-High (delegated)": "🟡🟠🤖 Medium-High (delegated)",
    }
    return risk_map.get(risk, f"⚪ {risk}")


def render_strategy_card(
    strategy: Dict[str, Any],
    key: Optional[str] = None,
    on_select: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Render a strategy selection card.

    Args:
        strategy: Dict with strategy data (name, description, stars, risk, etc.)
        key: Optional key for the select button
        on_select: Optional callback when strategy is selected
    """
    name = strategy.get("name", "Unknown Strategy")
    description = strategy.get("description", "")
    stars = strategy.get("stars", 3)
    risk = strategy.get("risk", "Medium")
    expected_return = strategy.get("expected_return", "N/A")
    best_for = strategy.get("best_for", "")
    tags = strategy.get("tags", [])

    with st.container():
        # Header
        st.markdown(f"### {name}")
        st.markdown(f"{render_stars(stars)}")

        # Info badges
        badge_col1, badge_col2 = st.columns([1, 1])
        with badge_col1:
            risk_color_map = {
                "Low": "green", "Low-Medium": "lightgreen",
                "Medium": "yellow", "Medium-High": "orange",
                "High": "red", "Medium (adaptive)": "yellow",
                "Medium-High (delegated)": "orange",
            }
            risk_color = risk_color_map.get(risk, "gray")
            st.markdown(f"**Risk:** :{risk_color}[{risk}]")
        with badge_col2:
            st.markdown(f"**Return:** {expected_return}")

        # Description
        st.markdown(f"*{description}*")

        # Best for
        if best_for:
            st.caption(f"**Best for:** {best_for}")

        # Tags
        if tags:
            tag_str = " ".join(f"`{tag}`" for tag in tags)
            st.markdown(f"Tags: {tag_str}")

        # Select button
        is_selected = st.session_state.get("selected_strategy") == name
        if is_selected:
            st.success("✅ Currently Selected")
        else:
            if st.button("Select Strategy", key=f"select_{key}" if key else None):
                st.session_state.selected_strategy = name
                if on_select:
                    on_select(name)
                st.rerun()

        st.markdown("---")


def render_strategy_grid(
    strategies: list[Dict[str, Any]],
    columns: int = 2,
    selected: Optional[str] = None,
) -> None:
    """
    Render a grid of strategy cards.

    Args:
        strategies: List of strategy dicts
        columns: Number of columns in the grid
        selected: Currently selected strategy name
    """
    cols = st.columns(columns)
    for idx, strategy in enumerate(strategies):
        with cols[idx % columns]:
            render_strategy_card(strategy, key=str(idx))
