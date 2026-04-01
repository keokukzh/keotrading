"""
KEOTrading Dashboard - Unified Signal Page
Systematic trading signal combining all 3 regime layers.
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

from src.agents.systematic_signal import (
    SystematicSignalGenerator,
    UnifiedSignal,
    LayerScore
)


def render_score_meter(score: int) -> None:
    """Render the unified score meter."""
    
    # Color based on score
    if score >= 2:
        color = "#00D4AA"  # Green
        label = "ACCUMULATE"
    elif score <= -2:
        color = "#FF6B6B"  # Red
        label = "REDUCE"
    else:
        color = "#FFD93D"  # Yellow
        label = "HOLD"
    
    # Score position (0 to 6 mapped to 0-100%)
    score_pos = (score + 3) / 6 * 100  # -3 to +3 → 0 to 100%
    
    st.markdown(f"""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="font-size: 96px; margin: 0; color: {color};">{score}</h1>
        <h2 style="color: {color}; margin: 5px 0;">{label}</h2>
        <p style="color: #888; margin: 5px 0;">out of ±3</p>
        
        <div style="background: linear-gradient(to right, #FF6B6B, #FFD93D, #00D4AA); 
                    height: 30px; border-radius: 15px; margin: 30px 0; position: relative;">
            <div style="position: absolute; left: {score_pos}%; top: -10px; 
                        width: 50px; height: 50px; background: white; 
                        border-radius: 50%; border: 4px solid {color};
                        transform: translateX(-50%);"></div>
        </div>
        
        <div style="display: flex; justify-content: space-between; color: #666; font-size: 12px;">
            <span>-3 (Bearish)</span>
            <span>0 (Neutral)</span>
            <span>+3 (Bullish)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_layer_score(layer: LayerScore) -> None:
    """Render individual layer score card."""
    
    score_colors = {
        1: "#00D4AA",
        0: "#FFD93D",
        -1: "#FF6B6B"
    }
    
    color = score_colors.get(layer.score, "#95A5A6")
    emoji = "🟢" if layer.score == 1 else "🔴" if layer.score == -1 else "🟡"
    
    st.markdown(f"""
    <div style="background: #222; border-radius: 10px; padding: 15px; margin: 5px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="margin: 0; color: #fff;">{layer.layer_name}</h4>
                <p style="margin: 5px 0 0 0; color: {color}; font-size: 18px;">
                    {emoji} {layer.score:+d} - {layer.value}
                </p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; color: #888; font-size: 12px;">{layer.details}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_historical_chart() -> None:
    """Render historical returns by score level."""
    
    scores = [-3, -2, -1, 0, 1, 2, 3]
    returns = [-16, -10, -3, 0, 4, 12, 18]
    colors = ["#FF6B6B", "#FF6B6B", "#FFD93D", "#95A5A6", "#4ECDC4", "#00D4AA", "#00D4AA"]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=[str(s) for s in scores],
        y=returns,
        marker_color=colors,
        text=[f"{r:+.0f}%" for r in returns],
        textposition="outside"
    ))
    
    fig.update_layout(
        title="Historical 30d Returns by Score Level",
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Score"),
        yaxis=dict(title="Expected Return (%)", showgrid=True, gridcolor="rgba(255,255,255,0.05)")
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_confidence_bar(confidence: float, hit_rate: float) -> None:
    """Render confidence metrics."""
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #222; border-radius: 10px;">
            <h3 style="color: #aaa; margin: 0;">Signal Confidence</h3>
            <h1 style="color: #00D4AA; margin: 10px 0;">{confidence:.0%}</h1>
            <p style="color: #666; font-size: 12px;">of maximum conviction</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #222; border-radius: 10px;">
            <h3 style="color: #aaa; margin: 0;">Historical Hit Rate</h3>
            <h1 style="color: #4ECDC4; margin: 10px 0;">{hit_rate:.0%}</h1>
            <p style="color: #666; font-size: 12px;">of signals correct</p>
        </div>
        """, unsafe_allow_html=True)


def render_unified_signal_page():
    """Render the Unified Signal page."""
    st.title("📊 Systematic Signal")
    st.markdown("Combined regime analysis: On-Chain + Macro + Sentiment")
    st.markdown("---")
    
    # Initialize generator
    if 'signal_generator' not in st.session_state:
        st.session_state['signal_generator'] = SystematicSignalGenerator()
    
    generator = st.session_state['signal_generator']
    
    # Generate signal
    with st.spinner("Generating unified signal..."):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            signal = loop.run_until_complete(generator.generate_signal())
            loop.close()
        except Exception as e:
            st.error(f"Error: {e}")
            return
    
    # Main score display
    render_score_meter(signal.total_score)
    
    st.markdown("---")
    
    # Trading recommendation
    rec_col1, rec_col2, rec_col3, rec_col4 = st.columns(4)
    
    with rec_col1:
        action_colors = {"ACCUMULATE": "#00D4AA", "HOLD": "#FFD93D", "REDUCE": "#FF6B6B"}
        action_color = action_colors.get(signal.action, "#95A5A6")
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: {action_color}22; 
                    border: 2px solid {action_color}; border-radius: 10px;">
            <h3 style="color: #aaa; margin: 0;">Action</h3>
            <h2 style="color: {action_color}; margin: 10px 0;">{signal.action}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with rec_col2:
        st.metric("Position Change", f"{signal.position_change:+.1f}%/week")
    
    with rec_col3:
        conviction_color = "#00D4AA" if signal.conviction == "HIGH" else "#FFD93D" if signal.conviction == "MEDIUM" else "#95A5A6"
        st.markdown(f"**Conviction:** :{conviction_color}[{signal.conviction}]")
    
    with rec_col4:
        st.metric("Sample Size", f"{signal.sample_size} occurrences")
    
    st.markdown("---")
    
    # Individual layer scores
    st.subheader("📊 Layer Scores")
    
    render_layer_score(signal.onchain_score)
    render_layer_score(signal.macro_score)
    render_layer_score(signal.sentiment_score)
    
    st.markdown("---")
    
    # Interpretation
    st.subheader("📝 Interpretation")
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #222, #333); 
                border-radius: 15px; padding: 20px;">
        <pre style="margin: 0; white-space: pre-wrap; color: #fff; font-family: inherit;">
{signal.interpretation}
        </pre>
    </div>
    """, unsafe_allow_html=True)
    
    # Warnings
    if signal.warnings:
        for warning in signal.warnings:
            st.warning(warning)
    
    st.markdown("---")
    
    # Historical stats
    st.subheader("📈 Historical Performance")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        expected_return = signal.historical_return * 100
        return_color = "#00D4AA" if expected_return >= 0 else "#FF6B6B"
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #222; border-radius: 10px;">
            <h3 style="color: #aaa; margin: 0;">Expected 30d Return</h3>
            <h1 style="color: {return_color}; margin: 10px 0;">{expected_return:+.1f}%</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        hit_color = "#00D4AA" if signal.hit_rate >= 0.6 else "#FFD93D"
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #222; border-radius: 10px;">
            <h3 style="color: #aaa; margin: 0;">Signal Accuracy</h3>
            <h1 style="color: {hit_color}; margin: 10px 0;">{signal.hit_rate:.0%}</h1>
            <p style="color: #666; font-size: 12px;">based on {signal.sample_size} occurrences</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Historical chart
    render_historical_chart()
    
    st.markdown("---")
    
    # Detailed breakdown
    st.subheader("🔍 Detailed Regime Data")
    
    with st.expander("On-Chain Regime Details"):
        oc = signal.onchain_signal
        st.write(f"**Regime:** {oc.regime.value}")
        st.write(f"**Confidence:** {oc.confidence:.0%}")
        st.write(f"**Expected Return:** {oc.forward_return_30d:.1%}")
        st.write(f"**Analysis:** {oc.interpretation}")
    
    with st.expander("Macro Regime Details"):
        mc = signal.macro_signal
        st.write(f"**Regime:** {mc.regime.value}")
        st.write(f"**Confidence:** {mc.confidence:.0%}")
        st.write(f"**Alignment Score:** {mc.alignment_score:+.2f}")
        st.write(f"**Tailwinds:** {', '.join(mc.tailwind_reasons) if mc.tailwind_reasons else 'None'}")
        st.write(f"**Headwinds:** {', '.join(mc.headwind_reasons) if mc.headwind_reasons else 'None'}")
    
    with st.expander("Sentiment Details"):
        sn = signal.sentiment_signal
        st.write(f"**Level:** {sn.level.value}")
        st.write(f"**F&G Value:** {sn.value}")
        st.write(f"**Contrarian Signal:** {sn.contrarian_signal}")
        st.write(f"**Historical Accuracy:** {sn.historical_accuracy:.0%}")
    
    st.markdown("---")
    
    # Trading rules explanation
    st.subheader("📋 Trading Rules")
    
    rules_col1, rules_col2, rules_col3 = st.columns(3)
    
    with rules_col1:
        st.success("""
        **Score ≥ +2**
        **→ ACCUMULATE**
        
        Add 2% to BTC position per week
        
        Example: $10,000 → add $200/week
        """)
    
    with rules_col2:
        st.info("""
        **Score -1 to +1**
        **→ HOLD**
        
        No action required
        
        Wait for clearer signals
        """)
    
    with rules_col3:
        st.error("""
        **Score ≤ -2**
        **→ REDUCE**
        
        Trim 2% from BTC position per week
        
        Example: $10,000 → remove $200/week
        """)
    
    st.markdown("---")
    
    # Last updated
    st.caption(f"Last updated: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Refresh button
    if st.button("🔄 Refresh Signal"):
        st.rerun()


if __name__ == "__main__":
    render_unified_signal_page()
