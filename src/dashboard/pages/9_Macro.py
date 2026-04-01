"""
KEOTrading Dashboard - Macro Analysis Page
Economic indicators and regime classification.
"""

from __future__ import annotations

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import plotly.graph_objects as go
import plotly.express as px

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.agents.macro_regime import (
    MacroRegimeDetector,
    MockMacroProvider,
    MacroRegime,
    MacroMetrics
)


def render_macro_page():
    """Render the Macro Analysis page."""
    st.title("🌍 Macro Analysis")
    st.markdown("Economic indicators and cross-regime analysis")
    st.markdown("---")
    
    # Initialize detector
    if 'macro_detector' not in st.session_state:
        st.session_state['macro_detector'] = MacroRegimeDetector(MockMacroProvider())
    
    detector = st.session_state['macro_detector']
    
    # Fetch data
    with st.spinner("Fetching macro data from FRED..."):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            signal = loop.run_until_complete(detector.get_macro_signal())
            metrics = loop.run_until_complete(detector.get_metrics())
            loop.close()
        except:
            signal = None
            metrics = MacroMetrics()
    
    # Get on-chain regime from session (if available)
    onchain_regime = st.session_state.get('onchain_regime', 'unknown')
    
    if signal:
        # Cross-check with on-chain
        aligned_signal = detector.analyze_alignment(onchain_regime)
        
        # Main indicator
        col1, col2 = st.columns([1, 1])
        
        with col1:
            regime_colors = {
                MacroRegime.CRYPTO_TAILWIND: ("🟢", "#00D4AA", "CRYPTO TAILWIND"),
                MacroRegime.CRYPTO_HEADWIND: ("🔴", "#FF6B6B", "CRYPTO HEADWIND"),
                MacroRegime.NEUTRAL: ("🟡", "#FFD93D", "NEUTRAL"),
                MacroRegime.UNKNOWN: ("⚪", "#95A5A6", "UNKNOWN"),
            }
            
            emoji, color, name = regime_colors.get(signal.regime, regime_colors[MacroRegime.UNKNOWN])
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {color}22, {color}11); 
                        border: 2px solid {color}; 
                        border-radius: 15px; 
                        padding: 20px; 
                        text-align: center;
                        margin: 10px 0;">
                <h1 style="font-size: 48px; margin: 0;">{emoji}</h1>
                <h2 style="color: {color}; margin: 5px 0;">{name}</h2>
                <p style="font-size: 24px; margin: 5px 0;">{signal.confidence:.0%} Confidence</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Alignment score
            alignment = signal.alignment_score
            align_color = "#00D4AA" if alignment > 0 else "#FF6B6B"
            
            st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
                <p style="color: #aaa; margin: 0;">Alignment Score</p>
                <h2 style="color: {align_color}; margin: 5px 0;">{alignment:+.2f}</h2>
                <p style="color: #666; font-size: 12px;">-1 = Bearish | 0 = Neutral | +1 = Bullish</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Cross-regime analysis
            st.subheader("🔗 Cross-Regime Check")
            
            confirm_colors = {
                "CONFIRMED": "#00D4AA",
                "CONTRADICTED": "#FF6B6B",
                "NEUTRAL": "#FFD93D"
            }
            
            confirm_color = confirm_colors.get(aligned_signal.confirmation_signal, "#95A5A6")
            
            st.markdown(f"""
            <div style="background: #222; border-radius: 10px; padding: 15px; margin: 10px 0;">
                <p style="color: #aaa; margin: 0;">On-Chain Regime</p>
                <h3 style="color: #fff; margin: 10px 0;">{onchain_regime.upper()}</h3>
                <hr style="border-color: #333;">
                <p style="color: #aaa; margin: 0;">Confirmation</p>
                <h3 style="color: {confirm_color}; margin: 10px 0;">
                    {aligned_signal.confirmation_signal or 'N/A'}
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Interpretation
            st.markdown(f"""
            <div style="background: #222; border-radius: 10px; padding: 15px; margin-top: 10px;">
                <p style="color: #aaa; margin: 0;">Analysis</p>
                <p style="margin: 10px 0 0 0;">{aligned_signal.interpretation}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Key indicators
    st.subheader("📊 Key Economic Indicators")
    
    if metrics:
        ind_col1, ind_col2 = st.columns([1, 1])
        
        with ind_col1:
            # USD Index (DXY)
            st.markdown("#### 💵 US Dollar Index (DXY)")
            
            dxy_color = "#00D4AA" if metrics.dxy_change_30d < 0 else "#FF6B6B"
            
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.metric("Current", f"{metrics.dxy_current:.2f}")
            with col_b:
                st.metric("30d Change", f"{metrics.dxy_change_30d:+.2f}%", delta_color="normal" if metrics.dxy_change_30d < 0 else "inverse")
            
            if metrics.dxy_change_30d < -1:
                st.success("🟢 Weak dollar = Bullish for crypto")
            elif metrics.dxy_change_30d > 1:
                st.error("🔴 Strong dollar = Bearish for crypto")
            else:
                st.info("🟡 Neutral dollar")
            
            st.markdown("---")
            
            # 10Y Yield
            st.markdown("#### 📈 10-Year Treasury Yield")
            
            yield_color = "#FF6B6B" if metrics.yield_10y_change_30d > 0 else "#00D4AA"
            
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.metric("Current", f"{metrics.yield_10y_current:.2f}%")
            with col_b:
                st.metric("30d Change", f"{metrics.yield_10y_change_30d:+.2f}%", delta_color="inverse" if metrics.yield_10y_change_30d < 0 else "normal")
            
            if metrics.yield_10y_change_30d < -2:
                st.success("🟢 Falling yields = Bullish (lower discount rate)")
            elif metrics.yield_10y_change_30d > 2:
                st.error("🔴 Rising yields = Bearish (higher discount rate)")
            else:
                st.info("🟡 Stable yields")
        
        with ind_col2:
            # VIX
            st.markdown("#### 📉 VIX (Volatility Index)")
            
            vix_color = "#00D4AA" if metrics.vix_current < 20 else "#FF6B6B"
            
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.metric("Current", f"{metrics.vix_current:.1f}")
            with col_b:
                st.metric("30d Change", f"{metrics.vix_change_30d:+.1f}%")
            
            if metrics.vix_current < 15:
                st.success("🟢 Low volatility = Risk-on environment")
            elif metrics.vix_current > 25:
                st.error("🔴 High volatility = Risk-off environment")
            else:
                st.info("🟡 Moderate volatility")
            
            st.markdown("---")
            
            # M2 Money Supply
            st.markdown("#### 💰 M2 Money Supply")
            
            m2_color = "#00D4AA" if metrics.m2_change_30d > 0 else "#FF6B6B"
            
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.metric("Current", f"${metrics.m2_current:.1f}T")
            with col_b:
                st.metric("30d Change", f"{metrics.m2_change_30d:+.2f}%")
            
            if metrics.m2_change_30d > 0.3:
                st.success("🟢 Expanding money supply = More liquidity")
            elif metrics.m2_change_30d < -0.2:
                st.error("🔴 Contracting money supply = Less liquidity")
            else:
                st.info("🟡 Stable money supply")
    
    st.markdown("---")
    
    # Tailwind/Headwind reasons
    if signal:
        reason_col1, reason_col2 = st.columns([1, 1])
        
        with reason_col1:
            st.markdown("#### 🟢 Tailwind Factors")
            if signal.tailwind_reasons:
                for reason in signal.tailwind_reasons:
                    st.write(f"• {reason}")
            else:
                st.info("No tailwind factors detected")
        
        with reason_col2:
            st.markdown("#### 🔴 Headwind Factors")
            if signal.headwind_reasons:
                for reason in signal.headwind_reasons:
                    st.write(f"• {reason}")
            else:
                st.info("No headwind factors detected")
    
    st.markdown("---")
    
    # Trading recommendations
    if signal:
        st.subheader("🎯 Trading Recommendations")
        
        recommendation = detector.get_trade_recommendation(signal)
        
        rec_col1, rec_col2, rec_col3 = st.columns(3)
        
        with rec_col1:
            bias_color = "#00D4AA" if recommendation['bias'] == "bullish" else "#FF6B6B" if recommendation['bias'] == "bearish" else "#FFD93D"
            st.markdown(f"**Bias:** {recommendation['bias'].upper()}")
            st.markdown(f"**Leverage:** {recommendation['leverage']}")
            st.markdown(f"**Position Size:** {recommendation['position_size']}")
        
        with rec_col2:
            st.markdown(f"**Hedging:** {recommendation['hedging']}")
            st.markdown(f"**Stop Loss:** {recommendation['stop_loss']}")
            st.markdown(f"**Take Profit:** {recommendation['take_profit']}")
        
        with rec_col3:
            st.info(f"💡 {recommendation['notes']}")
    
    st.markdown("---")
    
    # FRED Data source
    st.subheader("⚙️ Data Source")
    
    source_col1, source_col2 = st.columns([1, 1])
    
    with source_col1:
        data_source = st.selectbox(
            "Data Provider",
            ["FRED (Federal Reserve)", "Mock Data (Demo)"]
        )
        
        if data_source == "FRED (Federal Reserve)":
            fred_api_key = st.text_input("FRED API Key (optional)", type="password")
            st.caption("Get free API key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        else:
            st.info("Using mock data for demonstration")
    
    with source_col2:
        refresh_interval = st.number_input("Refresh (minutes)", value=15, min_value=5, max_value=60)
        
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    st.markdown("---")
    
    # Info box
    st.markdown("""
    <div style="background: #222; border-radius: 10px; padding: 15px;">
        <p style="margin: 0; color: #aaa;">
            📊 <strong>Macro Regime Analysis</strong><br>
            <small>
            Cross-checks: DXY (dollar strength), 10Y yield (risk-free rate), 
            VIX (market fear), M2 (liquidity).<br>
            Confirms or contradicts on-chain regime for stronger signals.
            </small>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render_macro_page()
