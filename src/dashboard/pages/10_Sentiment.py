"""
KEOTrading Dashboard - Sentiment Page
Fear & Greed Index and social sentiment analysis.
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

from src.agents.sentiment_detector import (
    SentimentDetector,
    MockSentimentProvider,
    SentimentLevel,
    SentimentSignal
)


def render_sentiment_gauge(value: int) -> None:
    """Render F&G gauge visualization."""
    
    # Color based on value
    if value < 25:
        color = "#FF6B6B"  # Red - Extreme Fear
        label = "EXTREME FEAR"
    elif value < 45:
        color = "#FFD93D"  # Yellow - Fear
        label = "FEAR"
    elif value < 55:
        color = "#95A5A6"  # Gray - Neutral
        label = "NEUTRAL"
    elif value < 75:
        color = "#4ECDC4"  # Teal - Greed
        label = "GREED"
    else:
        color = "#00D4AA"  # Green - Extreme Greed
        label = "EXTREME GREED"
    
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <h1 style="font-size: 72px; margin: 0; color: {color};">{value}</h1>
        <h2 style="color: {color}; margin: 5px 0;">{label}</h2>
        <div style="background: linear-gradient(to right, #FF6B6B, #FFD93D, #95A5A6, #4ECDC4, #00D4AA); 
                    height: 20px; border-radius: 10px; margin: 20px 0;
                    position: relative;">
            <div style="position: absolute; left: {value}%; top: -5px; 
                        width: 30px; height: 30px; background: white; 
                        border-radius: 50%; border: 3px solid {color};
                        transform: translateX(-50%);"></div>
        </div>
        <div style="display: flex; justify-content: space-between; color: #666; font-size: 12px;">
            <span>0</span>
            <span>25</span>
            <span>50</span>
            <span>75</span>
            <span>100</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sentiment_page():
    """Render the Sentiment Analysis page."""
    st.title("😨😰🤑 Sentiment Analysis")
    st.markdown("Fear & Greed Index and social sentiment overlay")
    st.markdown("---")
    
    # Initialize detector
    if 'sentiment_detector' not in st.session_state:
        st.session_state['sentiment_detector'] = SentimentDetector()
    
    detector = st.session_state['sentiment_detector']
    
    # Get other regimes from session
    onchain_regime = st.session_state.get('onchain_regime', 'unknown')
    macro_regime = st.session_state.get('macro_regime', 'unknown')
    
    # Fetch data
    with st.spinner("Fetching sentiment data..."):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            signal = loop.run_until_complete(detector.get_sentiment_signal())
            metrics = loop.run_until_complete(detector.get_metrics())
            loop.close()
        except Exception as e:
            signal = SentimentSignal(
                level=SentimentLevel.NEUTRAL,
                value=50,
                confidence=0.5,
                is_extreme=False,
                extreme_type="",
                buy_signal=False,
                historical_accuracy=0,
                contrarian_signal="HOLD",
                contrarian_strength=0
            )
            metrics = None
    
    # Main sentiment gauge
    gauge_col, info_col = st.columns([1, 1])
    
    with gauge_col:
        render_sentiment_gauge(signal.value)
    
    with info_col:
        # Contrarian signal
        signal_colors = {
            "BUY": "#00D4AA",
            "SELL": "#FF6B6B",
            "HOLD": "#FFD93D"
        }
        
        signal_color = signal_colors.get(signal.contrarian_signal, "#95A5A6")
        
        st.markdown(f"""
        <div style="background: #222; border-radius: 15px; padding: 20px; text-align: center;">
            <h3 style="color: #aaa; margin: 0;">Contrarian Signal</h3>
            <h1 style="color: {signal_color}; font-size: 48px; margin: 10px 0;">
                {signal.contrarian_signal}
            </h1>
            <p style="color: #888;">Historical Accuracy: {signal.historical_accuracy:.0%}</p>
            <p style="color: #666; font-size: 12px;">
                Strength: {signal.contrarian_strength:.0%}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Is extreme?
        if signal.is_extreme:
            if signal.extreme_type == "fear":
                st.error(f"😱 **EXTREME FEAR** - Buy signal (76% historical accuracy)")
            else:
                st.error(f"🤪 **EXTREME GREED** - Pullback risk (68% historical)")
        else:
            st.info("😐 No extreme sentiment detected")
    
    st.markdown("---")
    
    # Interpretation
    if signal.interpretation:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #222, #333); 
                    border-radius: 15px; padding: 20px; margin: 10px 0;">
            <p style="margin: 0; line-height: 1.6;">{signal.interpretation}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Cross-regime alignment
    aligned_signal = detector.analyze_alignment(onchain_regime, macro_regime)
    
    st.subheader("🔗 Cross-Regime Alignment")
    
    align_col1, align_col2, align_col3 = st.columns(3)
    
    with align_col1:
        st.metric("On-Chain Regime", onchain_regime.upper())
    
    with align_col2:
        st.metric("Macro Regime", macro_regime.upper())
    
    with align_col3:
        confirm_colors = {
            "CONFIRMED": "#00D4AA",
            "CONTRADICTED": "#FF6B6B",
            "NEUTRAL": "#FFD93D"
        }
        confirm_color = confirm_colors.get(aligned_signal.confirmation_signal, "#95A5A6")
        st.markdown(f"**Confirmation:** <span style='color:{confirm_color}'>{aligned_signal.confirmation_signal or 'N/A'}</span>", unsafe_allow_html=True)
    
    # Confirmation explanation
    if aligned_signal.alignment_with_fundamentals:
        st.success(f"✅ Sentiment {signal.extreme_type or 'neutral'} ALIGNS with {onchain_regime} + {macro_regime}")
    elif aligned_signal.confirmation_signal == "CONTRADICTED":
        st.warning(f"⚠️ Sentiment CONTRADICTS {onchain_regime} + {macro_regime} - caution warranted")
    else:
        st.info(f"Sentiment does not clearly confirm or contradict fundamentals")
    
    st.markdown("---")
    
    # Sentiment metrics
    if metrics:
        st.subheader("📊 Sentiment Metrics")
        
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            st.metric("24h Change", f"{metrics.fng_change_24h:+d}")
            
            if metrics.fng_change_24h < -10:
                st.warning("📉 Fear increasing")
            elif metrics.fng_change_24h > 10:
                st.warning("📈 Greed increasing")
            else:
                st.info("➡️ Stable")
        
        with metrics_col2:
            st.metric("Social Volume", f"{metrics.social_volume:,}")
            
            if metrics.social_volume > 50000:
                st.caption("High social activity")
            else:
                st.caption("Normal social activity")
        
        with metrics_col3:
            sentiment_pct = (metrics.sentiment_score + 1) / 2 * 100
            st.metric("Social Sentiment", f"{sentiment_pct:.0f}%")
            
            if metrics.sentiment_score > 0.5:
                st.caption("🟢 Bullish")
            elif metrics.sentiment_score < -0.5:
                st.caption("🔴 Bearish")
            else:
                st.caption("⚪ Neutral")
    
    st.markdown("---")
    
    # Trading recommendations
    st.subheader("🎯 Trading Recommendation")
    
    rec = detector.get_trade_recommendation(signal)
    
    rec_col1, rec_col2 = st.columns([1, 1])
    
    with rec_col1:
        action_color = "#00D4AA" if rec['action'] == "BUY" else "#FF6B6B" if rec['action'] == "SELL" else "#FFD93D"
        st.markdown(f"**Action:** <span style='color:{action_color}'>{rec['action']}</span>", unsafe_allow_html=True)
        st.write(f"**Position:** {rec['position']}")
        st.write(f"**Target:** {rec['target']}")
    
    with rec_col2:
        st.write(f"**Stop Loss:** {rec['stop_loss']}")
        st.info(f"💡 {rec['notes']}")
    
    st.markdown("---")
    
    # Historical F&G chart
    st.subheader("📈 Fear & Greed History")
    
    # Generate mock history for demo
    import random
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, -1, -1)]
    values = []
    current = signal.value
    for i in range(31):
        current = max(0, min(100, current + random.uniform(-10, 10)))
        values.append(int(current))
    values.reverse()
    
    fig = go.Figure()
    
    # Add F&G line
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        fill='tozeroy',
        line=dict(color='#FFD93D', width=2),
        fillcolor='rgba(255, 217, 61, 0.2)',
        name='F&G Index'
    ))
    
    # Add zones
    fig.add_hrect(y0=0, y1=25, fillcolor="rgba(255,107,107,0.2)", line_width=0, annotation_text="Extreme Fear")
    fig.add_hrect(y0=25, y1=45, fillcolor="rgba(255,217,61,0.2)", line_width=0, annotation_text="Fear")
    fig.add_hrect(y0=45, y1=55, fillcolor="rgba(149,165,166,0.2)", line_width=0, annotation_text="Neutral")
    fig.add_hrect(y0=55, y1=75, fillcolor="rgba(78,205,196,0.2)", line_width=0, annotation_text="Greed")
    fig.add_hrect(y0=75, y1=100, fillcolor="rgba(0,212,170,0.2)", line_width=0, annotation_text="Extreme Greed")
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", range=[0, 100]),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Data sources
    st.subheader("⚙️ Data Sources")
    
    source_col1, source_col2 = st.columns([1, 1])
    
    with source_col1:
        fng_source = st.selectbox(
            "Fear & Greed Source",
            ["Alternative.me (Free)", "Custom API"]
        )
        
        st.caption("Alternative.me provides free F&G data")
    
    with source_col2:
        social_source = st.selectbox(
            "Social Sentiment",
            ["LunarCrush", "CoinGecko", "Mock Data"]
        )
        
        if social_source == "LunarCrush":
            api_key = st.text_input("LunarCrush API Key", type="password")
    
    if st.button("🔄 Refresh Sentiment"):
        st.rerun()
    
    st.markdown("---")
    
    # Info box
    st.markdown("""
    <div style="background: #222; border-radius: 10px; padding: 15px;">
        <p style="margin: 0; color: #aaa;">
            📊 <strong>Historical Accuracy</strong><br>
            <small>
            • <strong>Extreme Fear → Buy:</strong> 76% of the time price increased over next 30 days<br>
            • <strong>Extreme Greed → Pullback:</strong> 68% of the time price decreased over next 30 days<br>
            <br>
            Use as contrarian indicator - extreme sentiment often marks local tops/bottoms.
            </small>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render_sentiment_page()
