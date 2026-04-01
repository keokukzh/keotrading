"""
KEOTrading Dashboard - Main Streamlit Application
=================================================
Multi-agent crypto trading dashboard with LLM-enhanced strategy selection.
"""

from __future__ import annotations

import streamlit as st
from typing import Optional

# Page config
st.set_page_config(
    page_title="KEOTrading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "selected_strategy" not in st.session_state:
        st.session_state.selected_strategy = "LP Arbitrage (hzjken)"
    if "llm_provider" not in st.session_state:
        st.session_state.llm_provider = "openai"
    if "api_base_url" not in st.session_state:
        st.session_state.api_base_url = "http://localhost:8000"
    if "refresh_interval" not in st.session_state:
        st.session_state.refresh_interval = 30
    if "agents" not in st.session_state:
        st.session_state.agents = []
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = {}


init_session_state()


def main() -> None:
    """Render the main dashboard layout."""
    st.sidebar.title("📊 KEOTrading")
    st.sidebar.markdown("---")

    # Navigation is handled by Streamlit's pages feature
    st.sidebar.markdown("### Navigation")
    st.sidebar.info(
        "Use the menu above to navigate between pages:\n"
        "- **Overview** - System status & P&L\n"
        "- **Strategies** - Strategy selector\n"
        "- **Agents** - Agent monitoring\n"
        "- **Portfolio** - Portfolio management\n"
        "- **Settings** - Configuration"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Stats")

    # Quick stats in sidebar
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Total P&L", "$12,345", "+8.2%")
    with col2:
        st.metric("Active Agents", "5", "1 paused")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "### 🐻 Bobro AI Assistant\n"
        "*Autopilot enabled*"
    )


if __name__ == "__main__":
    main()
