"""
KEOTrading Dashboard - Settings Page
=====================================
Configuration, API keys, LLM provider settings, and dashboard preferences.
"""

from __future__ import annotations

import streamlit as st
from typing import Dict, Any, Optional


def render_settings() -> None:
    """Render the Settings page."""
    st.title("⚙️ Settings")
    st.markdown("Configure your dashboard, API connections, and LLM providers.")
    st.markdown("---")

    # LLM Provider Settings
    st.subheader("🤖 LLM Provider Configuration")
    st.markdown(
        "Configure the LLM backend for the Strategy Advisor. "
        "Supports OpenAI, Anthropic, and local Ollama."
    )

    llm_col1, llm_col2 = st.columns([1, 1])
    with llm_col1:
        llm_provider = st.selectbox(
            "Provider",
            options=["openai", "anthropic", "ollama"],
            index=0,
            help="Select LLM provider",
        )
        if llm_provider == "openai":
            st.text_input("OpenAI API Key", type="password", value="", placeholder="sk-...")
            st.selectbox("Model", options=["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        elif llm_provider == "anthropic":
            st.text_input("Anthropic API Key", type="password", value="", placeholder="sk-ant-...")
            st.selectbox("Model", options=["claude-opus-4", "claude-sonnet-4", "claude-haiku"])
        elif llm_provider == "ollama":
            st.text_input("Ollama URL", value="http://localhost:11434")
            st.selectbox("Model", options=["llama3.3", "mistral", "codellama", "mixtral"])

    with llm_col2:
        st.number_input("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
        st.number_input("Max Tokens", min_value=256, max_value=8192, value=2048, step=256)
        st.checkbox("Enable streaming", value=True)
        st.checkbox("Cache responses", value=True)

    st.markdown("---")

    # API Configuration
    st.subheader("🌐 API Configuration")
    api_col1, api_col2 = st.columns([1, 1])
    with api_col1:
        st.text_input("API Base URL", value="http://localhost:8000")
        st.number_input("API Port", min_value=1024, max_value=65535, value=8000)
        st.text_input("API Username", value="admin")
    with api_col2:
        st.text_input("API Password", type="password", value="")
        st.number_input("Request Timeout (s)", min_value=5, max_value=120, value=30)
        st.checkbox("Enable HTTPS", value=False)

    st.markdown("---")

    # Exchange API Keys
    st.subheader("🔑 Exchange API Keys")
    st.caption("API keys are stored securely and never exposed to the frontend.")

    exchanges = {
        "Binance": {"enabled": True, "has_keys": True},
        "Bybit": {"enabled": True, "has_keys": True},
        "OKX": {"enabled": False, "has_keys": False},
        "Raydium (Solana)": {"enabled": True, "has_keys": True},
        "Orca (Solana)": {"enabled": True, "has_keys": True},
    }

    for exchange, info in exchanges.items():
        ex_col1, ex_col2, ex_col3 = st.columns([2, 1, 1])
        with ex_col1:
            st.checkbox(f"**{exchange}**", value=info["enabled"])
        with ex_col2:
            if info["has_keys"]:
                st.button("🔄 Rotate Keys", key=f"rotate_{exchange}")
        with ex_col3:
            status = "🟢 Connected" if info["has_keys"] else "⚪ Not configured"
            st.markdown(f"<span style='font-size:0.85em'>{status}</span>", unsafe_allow_html=True)

    st.markdown("---")

    # Dashboard Settings
    st.subheader("📊 Dashboard Preferences")
    dash_col1, dash_col2 = st.columns([1, 1])
    with dash_col1:
        st.number_input("Refresh Interval (seconds)", min_value=5, max_value=300, value=30, step=5)
        st.selectbox("Theme", options=["Dark", "Light", "System"])
        st.selectbox("Currency", options=["USD", "EUR", "BTC", "ETH"])
    with dash_col2:
        st.checkbox("Enable sound notifications", value=False)
        st.checkbox("Show P&L in header", value=True)
        st.checkbox("Auto-refresh charts", value=True)

    st.markdown("---")

    # Risk Settings
    st.subheader("⚠️ Risk Limits")
    risk_col1, risk_col2 = st.columns([1, 1])
    with risk_col1:
        st.number_input("Max Daily Loss ($)", min_value=0, value=1000, step=100)
        st.number_input("Max Position Size (%)", min_value=1, max_value=100, value=20)
    with risk_col2:
        st.number_input("Max Open Positions", min_value=1, max_value=100, value=10)
        st.number_input("Emergency Stop P&L ($)", min_value=-10000, value=-5000, step=500)

    st.markdown("---")

    # Save/Reset
    save_col1, save_col2, save_col3 = st.columns([1, 1, 2])
    with save_col1:
        st.button("💾 Save Settings", type="primary")
    with save_col2:
        st.button("🔄 Reset to Defaults")
    with save_col3:
        st.button("📤 Export Config")

    st.markdown("---")
    st.caption(
        "Settings are persisted to `configs/dashboard.yaml`. "
        "Changes take effect on next page refresh."
    )


if __name__ == "__main__":
    render_settings()
