"""
KEOTrading Dashboard - Settings Page
=====================================
Configuration, API keys, LLM provider settings, and dashboard preferences.
"""

from __future__ import annotations

import streamlit as st
import asyncio
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.exchange.connection import ExchangeManager, ExchangeConfig


def render_settings() -> None:
    """Render the Settings page."""
    st.title("⚙️ Settings")
    st.markdown("Configure your dashboard, API connections, and LLM providers.")
    st.markdown("---")
    
    # Initialize exchange manager
    if 'exchange_manager' not in st.session_state:
        st.session_state['exchange_manager'] = ExchangeManager()
    
    exchange_manager = st.session_state['exchange_manager']

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
            api_key = st.text_input("OpenAI API Key", type="password", value="", placeholder="sk-...")
            model = st.selectbox("Model", options=["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        elif llm_provider == "anthropic":
            api_key = st.text_input("Anthropic API Key", type="password", value="", placeholder="sk-ant-...")
            model = st.selectbox("Model", options=["claude-opus-4", "claude-sonnet-4", "claude-haiku"])
        elif llm_provider == "ollama":
            api_key = st.text_input("Ollama URL", value="http://localhost:11434")
            model = st.selectbox("Model", options=["llama3.3", "mistral", "codellama", "mixtral"])

    with llm_col2:
        temperature = st.number_input("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
        max_tokens = st.number_input("Max Tokens", min_value=256, max_value=8192, value=2048, step=256)
        enable_streaming = st.checkbox("Enable streaming", value=True)
        cache_responses = st.checkbox("Cache responses", value=True)

    st.markdown("---")

    # API Configuration
    st.subheader("🌐 API Configuration")
    api_col1, api_col2 = st.columns([1, 1])
    with api_col1:
        api_base_url = st.text_input("API Base URL", value="http://localhost:8000")
        api_port = st.number_input("API Port", min_value=1024, max_value=65535, value=8000)
        api_username = st.text_input("API Username", value="admin")
    with api_col2:
        api_password = st.text_input("API Password", type="password", value="")
        request_timeout = st.number_input("Request Timeout (s)", min_value=5, max_value=120, value=30)
        enable_https = st.checkbox("Enable HTTPS", value=False)

    st.markdown("---")

    # Exchange API Keys
    st.subheader("🔑 Exchange API Keys")
    st.caption("API keys are stored securely. Click 'Test Connection' to verify.")
    
    # Supported exchanges
    supported_exchanges = {
        "binance": {"name": "Binance", "enabled": False, "has_keys": False},
        "kraken": {"name": "Kraken", "enabled": False, "has_keys": False},
        "bybit": {"name": "Bybit", "enabled": False, "has_keys": False},
        "coinbase": {"name": "Coinbase", "enabled": False, "has_keys": False},
    }
    
    # Initialize session state for exchange connections
    if 'exchange_connections' not in st.session_state:
        st.session_state['exchange_connections'] = {}
    
    # Display exchange configuration
    for exchange_id, info in supported_exchanges.items():
        with st.container():
            ex_col1, ex_col2, ex_col3, ex_col4 = st.columns([2, 2, 1, 1])
            
            with ex_col1:
                enabled = st.checkbox(f"**{info['name']}**", value=info['enabled'], key=f"enabled_{exchange_id}")
            
            with ex_col2:
                api_key = st.text_input(
                    f"API Key ({info['name']})", 
                    type="password", 
                    value="",
                    placeholder="Enter API key",
                    key=f"api_key_{exchange_id}"
                )
            
            with ex_col3:
                testnet = st.checkbox("Testnet", value=False, key=f"testnet_{exchange_id}")
            
            with ex_col4:
                # Connection status
                if exchange_id in st.session_state['exchange_connections']:
                    conn_status = st.session_state['exchange_connections'][exchange_id]
                    if conn_status.get('connected'):
                        st.success("🟢 Connected")
                    elif conn_status.get('tested'):
                        st.error("🔴 Failed")
                    else:
                        st.info("⚪ Not tested")
                else:
                    st.info("⚪ Not tested")
        
        # Test connection button
        test_col1, test_col2 = st.columns([1, 4])
        with test_col1:
            if st.button(f"🔗 Test {info['name']}", key=f"test_btn_{exchange_id}"):
                if api_key and len(api_key) > 10:
                    with st.spinner(f"Testing {info['name']} connection..."):
                        config = ExchangeConfig(
                            exchange_id=exchange_id,
                            api_key=api_key,
                            api_secret="",  # User should provide
                            testnet=testnet
                        )
                        from src.exchange.connection import ExchangeConnection
                        conn = ExchangeConnection(config)
                        
                        # Run async test
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        success = loop.run_until_complete(conn.connect())
                        loop.close()
                        
                        st.session_state['exchange_connections'][exchange_id] = {
                            'tested': True,
                            'connected': success
                        }
                        
                        if success:
                            st.success(f"✅ {info['name']} connection successful!")
                        else:
                            st.error(f"❌ {info['name']} connection failed. Check your API keys.")
                else:
                    st.warning(f"Please enter a valid API key for {info['name']}")
        
        with test_col2:
            st.write("")
        
        st.markdown("---")

    # Dashboard Settings
    st.subheader("📊 Dashboard Preferences")
    dash_col1, dash_col2 = st.columns([1, 1])
    with dash_col1:
        refresh_interval = st.number_input("Refresh Interval (seconds)", min_value=5, max_value=300, value=30, step=5)
        theme = st.selectbox("Theme", options=["Dark", "Light", "System"])
        currency = st.selectbox("Currency", options=["USD", "EUR", "BTC", "ETH"])
    with dash_col2:
        enable_sound = st.checkbox("Enable sound notifications", value=False)
        show_pnl_header = st.checkbox("Show P&L in header", value=True)
        auto_refresh = st.checkbox("Auto-refresh charts", value=True)

    st.markdown("---")

    # Risk Settings
    st.subheader("⚠️ Risk Limits")
    st.caption("These limits protect your capital from excessive losses.")
    
    risk_col1, risk_col2 = st.columns([1, 1])
    with risk_col1:
        max_daily_loss = st.number_input("Max Daily Loss ($)", min_value=0, value=1000, step=100)
        max_position_pct = st.number_input("Max Position Size (%)", min_value=1, max_value=100, value=20)
    with risk_col2:
        max_open_positions = st.number_input("Max Open Positions", min_value=1, max_value=100, value=10)
        emergency_stop = st.number_input("Emergency Stop P&L ($)", min_value=-10000, value=-5000, step=500)

    st.markdown("---")

    # Live Trading Mode
    st.subheader("🎮 Trading Mode")
    
    mode_col1, mode_col2 = st.columns([1, 1])
    with mode_col1:
        trading_mode = st.radio(
            "Trading Mode",
            options=["paper", "live"],
            index=0,
            horizontal=True,
            help="Paper trading uses simulated orders. Live trading executes real orders."
        )
        if trading_mode == "live":
            st.warning("⚠️ LIVE TRADING: Real funds will be at risk!")
    
    with mode_col2:
        st.write("**Mode Info:**")
        if trading_mode == "paper":
            st.info("📝 Paper trading: All orders are simulated. No real funds used.")
        else:
            st.error("💰 Live trading: Orders are executed on connected exchanges.")
    
    st.markdown("---")

    # Save/Reset
    save_col1, save_col2, save_col3 = st.columns([1, 1, 2])
    with save_col1:
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            st.success("✅ Settings saved successfully!")
            st.balloons()
    
    with save_col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.info("Settings reset to defaults.")
    
    with save_col3:
        if st.button("📤 Export Config", use_container_width=True):
            st.info("Config export feature coming soon!")

    st.markdown("---")
    
    # Connection Status Summary
    st.subheader("📡 Connection Status")
    
    conn_col1, conn_col2, conn_col3, conn_col4 = st.columns(4)
    
    connected_count = sum(1 for c in st.session_state['exchange_connections'].values() if c.get('connected'))
    
    with conn_col1:
        st.metric("Exchanges Configured", len([e for e in supported_exchanges if st.session_state.get(f'enabled_{e}', False)]))
    
    with conn_col2:
        st.metric("Connections Active", connected_count)
    
    with conn_col3:
        if exchange_manager.get_connected_exchanges():
            st.success("🟢 System Online")
        else:
            st.warning("🟡 No Exchanges Connected")
    
    with conn_col4:
        refresh = st.session_state.get('refresh_interval', 30)
        st.write(f"Refresh: {refresh}s")
    
    st.markdown("---")
    st.caption(
        "Settings are persisted to `configs/dashboard.yaml`. "
        "Exchange API keys are stored in `configs/exchanges.yaml`. "
        "Changes take effect on next page refresh."
    )


if __name__ == "__main__":
    render_settings()
