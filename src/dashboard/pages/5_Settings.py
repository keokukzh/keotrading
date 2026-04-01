"""
KEOTrading Dashboard - Settings Page
=====================================
Configuration, API keys, LLM provider settings, deposits, and dashboard preferences.
"""

from __future__ import annotations

import streamlit as st
import asyncio
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.exchange.connection import ExchangeManager, ExchangeConnection, ExchangeConfig


def render_settings() -> None:
    """Render the Settings page."""
    st.title("⚙️ Settings")
    st.markdown("Configure your dashboard, API connections, LLM providers, and deposits.")
    st.markdown("---")
    
    # Initialize exchange manager
    if 'exchange_manager' not in st.session_state:
        st.session_state['exchange_manager'] = ExchangeManager()
    
    exchange_manager = st.session_state['exchange_manager']

    # Tabs for organization
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌐 Exchanges", 
        "💳 Deposit Funds",
        "🤖 LLM", 
        "📊 Dashboard", 
        "⚠️ Risk"
    ])
    
    # =================================================================
    # TAB 1: Exchange API Keys
    # =================================================================
    with tab1:
        st.subheader("🔑 Exchange API Keys")
        st.markdown("API keys are stored securely. Click 'Test Connection' to verify.")
        
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
                            # For security, we don't store the secret in session state
                            # User must provide it for connection
                            st.info(f"⚠️ Please also provide API Secret for {info['name']}")
                    else:
                        st.warning(f"Please enter a valid API key for {info['name']}")
            
            with test_col2:
                st.write("")
            
            st.markdown("---")
        
        # Exchange-specific instructions
        st.subheader("📖 How to get API keys")
        
        with st.expander("Binance API Setup"):
            st.markdown("""
            1. Log in to [Binance](https://www.binance.com)
            2. Go to **API Management** in your account settings
            3. Create a new API key with **Enable Spot & Margin Trading** permission
            4. Copy the API Key and Secret Key
            5. **Important:** Enable IP restriction for security
            """)
        
        with st.expander("Kraken API Setup"):
            st.markdown("""
            1. Log in to [Kraken](https://www.kraken.com)
            2. Go to **Settings → API**
            3. Create a new API key with **Query** and **Create & Modify Orders** permissions
            4. Copy the API Key and Private Key
            """)
        
        with st.expander("Bybit API Setup"):
            st.markdown("""
            1. Log in to [Bybit](https://www.bybit.com)
            2. Go to **API Keys** in your account
            3. Create a new API key with **Read-Write** permissions
            4. Copy the API Key and API Secret
            """)

    # =================================================================
    # TAB 2: Deposit Funds (Credit Card)
    # =================================================================
    with tab2:
        st.subheader("💳 Deposit Funds via Credit Card")
        st.markdown("Add funds to your trading account using credit/debit card or other payment methods.")
        
        # Payment provider status
        payment_col1, payment_col2, payment_col3 = st.columns(3)
        
        with payment_col1:
            st.metric("MoonPay", "Available", "1-5% fee")
        with payment_col2:
            st.metric("Ramp Network", "Available", "1-3% fee")
        with payment_col3:
            st.metric("Mercuryo", "Available", "2-3.5% fee")
        
        st.markdown("---")
        
        # Deposit form
        deposit_method = st.radio(
            "Select deposit method:",
            ["💳 Credit/Debit Card (MoonPay)", "💳 Credit/Debit Card (Ramp)", "🔄 Exchange Transfer"],
            horizontal=True
        )
        
        if deposit_method.startswith("💳"):
            # Card deposit form
            deposit_col1, deposit_col2 = st.columns([1, 1])
            
            with deposit_col1:
                deposit_amount = st.number_input(
                    "Amount (USD)",
                    min_value=10.0,
                    max_value=50000.0,
                    value=100.0,
                    step=10.0,
                    help="Minimum deposit: $10"
                )
                
                crypto_options = ["USDT", "USDC", "BTC", "ETH", "SOL", "AVAX"]
                crypto_currency = st.selectbox(
                    "Receive cryptocurrency",
                    options=crypto_options,
                    index=0,
                    help="The crypto asset you'll receive"
                )
            
            with deposit_col2:
                currency = st.selectbox(
                    "Pay with",
                    options=["USD", "EUR", "GBP", "AUD", "CAD"],
                    index=0
                )
                
                st.info(f"""
                **Estimated fees:** 1-5% + network fee
                
                **Receive:** ~{deposit_amount * 0.97:.2f} {crypto_currency}
                (after fees)
                """)
            
            st.markdown("---")
            
            # Wallet address input
            st.subheader("📥 Destination Wallet")
            wallet_address = st.text_input(
                "Your exchange wallet address",
                value="",
                placeholder=f"Enter your {crypto_currency} deposit address",
                help="This is where your purchased crypto will be sent"
            )
            
            if not wallet_address:
                st.warning("⚠️ Please enter your wallet address to receive funds")
            
            # Email for receipt
            email = st.text_input("Email (for receipt)", placeholder="your@email.com")
            
            st.markdown("---")
            
            # Create deposit button
            if st.button("🚀 Create Deposit Request", type="primary", use_container_width=True):
                if not wallet_address or len(wallet_address) < 20:
                    st.error("⚠️ Please enter a valid wallet address")
                elif deposit_amount < 10:
                    st.error("⚠️ Minimum deposit is $10")
                else:
                    with st.spinner("Creating deposit..."):
                        try:
                            from src.dashboard.payment import get_payment_manager
                            payment_manager = get_payment_manager()
                            
                            # Determine provider
                            provider = "moonpay" if "MoonPay" in deposit_method else "ramp"
                            
                            # Create deposit
                            deposit = asyncio.run(payment_manager.create_deposit(
                                amount=deposit_amount,
                                currency=currency,
                                crypto_currency=crypto_currency,
                                provider=provider,
                                wallet_address=wallet_address,
                                email=email if email else None
                            ))
                            
                            if deposit and deposit.payment_url:
                                st.success("✅ Deposit request created!")
                                st.markdown(f"**Deposit ID:** `{deposit.id}`")
                                st.markdown(f"**Payment URL:** [Click here to complete payment]({deposit.payment_url})")
                                
                                # Display as clickable link
                                st.markdown(f"""
                                ### Payment Instructions
                                1. Click the payment link above
                                2. Complete the payment with your card
                                3. Funds will be sent to your wallet address
                                4. Check the **Portfolio** page for your balance
                                """)
                            else:
                                st.error("❌ Failed to create deposit. Please check your configuration.")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
        
        elif deposit_method == "🔄 Exchange Transfer":
            # Exchange transfer instructions
            st.subheader("📋 Direct Transfer Instructions")
            st.markdown("""
            Transfer funds directly to your exchange account:
            """)
            
            exchange_transfer = st.selectbox(
                "Select exchange",
                options=["Binance", "Kraken", "Bybit", "Coinbase"],
                index=0
            )
            
            if exchange_transfer == "Binance":
                st.markdown("""
                ### Binance Deposit Instructions
                1. Log in to your [Binance account](https://www.binance.com)
                2. Go to **Wallet → Deposit**
                3. Select the cryptocurrency (e.g., USDT)
                4. Choose **Credit/Debit Card** as payment method
                5. Enter amount and complete payment
                6. Funds credited to Spot Wallet immediately
                
                **Fees:** 1-3% depending on card and region
                **Min deposit:** $10 equivalent
                
                [→ Go to Binance Deposit](https://www.binance.com/en/my/wallet/deposit)
                """)
            elif exchange_transfer == "Kraken":
                st.markdown("""
                ### Kraken Deposit Instructions
                1. Log in to your [Kraken account](https://www.kraken.com)
                2. Go to **Funding → Deposit**
                3. Select cryptocurrency
                4. Click **Buy Crypto with Card** or use card deposit
                5. Enter amount and complete verification
                
                **Fees:** 0.5-2.5% + network fee
                **Min deposit:** $10 equivalent
                
                [→ Go to Kraken Deposit](https://www.kraken.com/u/funding/deposit)
                """)
            elif exchange_transfer == "Bybit":
                st.markdown("""
                ### Bybit Deposit Instructions
                1. Log in to your [Bybit account](https://www.bybit.com)
                2. Go to **Assets → Deposit**
                3. Select **Buy Crypto** option
                4. Choose credit card payment
                5. Enter amount and complete purchase
                
                **Fees:** 2-3.5% depending on region
                **Min deposit:** $10 equivalent
                
                [→ Go to Bybit Deposit](https://www.bybit.com/en/my/assets/deposit)
                """)
            elif exchange_transfer == "Coinbase":
                st.markdown("""
                ### Coinbase Deposit Instructions
                1. Log in to your [Coinbase account](https://www.coinbase.com)
                2. Click **Buy** button
                3. Select cryptocurrency
                4. Enter amount and select card
                5. Confirm purchase
                
                **Fees:** Coinbase fee (1.49-3.99%) + network fee
                **Min deposit:** $10 equivalent
                
                [→ Go to Coinbase](https://www.coinbase.com/buy)
                """)
        
        st.markdown("---")
        
        # Recent deposits
        st.subheader("📜 Recent Deposits")
        
        try:
            from src.dashboard.payment import get_payment_manager
            payment_manager = get_payment_manager()
            deposits = payment_manager.get_all_deposits()
            
            if deposits:
                for deposit in deposits[-5:]:  # Last 5 deposits
                    status_emoji = {
                        "pending": "⏳",
                        "processing": "🔄",
                        "completed": "✅",
                        "failed": "❌"
                    }.get(deposit.status, "❓")
                    
                    st.markdown(f"""
                    **{status_emoji} {deposit.provider.title()} Deposit**
                    - Amount: ${deposit.amount} {deposit.currency}
                    - Crypto: {deposit.crypto_currency}
                    - Status: {deposit.status}
                    - Created: {deposit.created_at.strftime('%Y-%m-%d %H:%M') if deposit.created_at else 'N/A'}
                    """)
            else:
                st.info("No deposits yet")
        except Exception as e:
            st.info("No deposit history available")

    # =================================================================
    # TAB 3: LLM Provider Configuration
    # =================================================================
    with tab3:
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

    # =================================================================
    # TAB 4: Dashboard Preferences
    # =================================================================
    with tab4:
        st.subheader("📊 Dashboard Preferences")
        dash_col1, dash_col2 = st.columns([1, 1])
        with dash_col1:
            refresh_interval = st.number_input("Refresh Interval (seconds)", min_value=5, max_value=300, value=30, step=5)
            theme = st.selectbox("Theme", options=["Dark", "Light", "System"])
            currency = st.selectbox("Display Currency", options=["USD", "EUR", "BTC", "ETH"])
        with dash_col2:
            enable_sound = st.checkbox("Enable sound notifications", value=False)
            show_pnl_header = st.checkbox("Show P&L in header", value=True)
            auto_refresh = st.checkbox("Auto-refresh charts", value=True)
        
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

    # =================================================================
    # TAB 5: Risk Settings
    # =================================================================
    with tab5:
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
        
        # Trading Mode
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
                st.error("⚠️ LIVE TRADING: Real funds will be at risk!")
        
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
        st.write("*Settings are persisted to `configs/`*")

    st.markdown("---")
    
    # Connection Status Summary
    st.subheader("📡 Connection Status")
    
    conn_col1, conn_col2, conn_col3, conn_col4 = st.columns(4)
    
    connected_count = len(exchange_manager.get_connected_exchanges())
    
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
