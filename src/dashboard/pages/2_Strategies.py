"""
KEOTrading Dashboard - Strategies Page
========================================
Strategy selector with 8 options, star ratings, risk levels, and LLM advisor.
"""

from __future__ import annotations

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from src.dashboard.llm_advisor import LLMStrategyAdvisor
except ImportError:
    LLMStrategyAdvisor = None


STRATEGIES: list[Dict[str, Any]] = [
    {
        "name": "LP Arbitrage (hzjken)",
        "description": "Liquidity pool arbitrage exploiting price differences across DEXs. High capital efficiency with controlled IL risk.",
        "stars": 5,
        "risk": "Medium",
        "expected_return": "15-25% APR",
        "best_for": "Stable pairs, high-volatility assets",
        "tags": ["arbitrage", "DeFi", "LP"],
    },
    {
        "name": "Scalping (Mean Reversion)",
        "description": "Fast-paced mean reversion strategy exploiting short-term price oscillations. Requires tight spread pairs.",
        "stars": 4,
        "risk": "Medium-High",
        "expected_return": "8-15% monthly",
        "best_for": "High-liquidity pairs, low fees",
        "tags": ["scalping", "mean-reversion", "CEX/DEX"],
    },
    {
        "name": "Grid Trading",
        "description": "Automated grid orders at preset price levels. Profits from volatility without directional bias.",
        "stars": 4,
        "risk": "Low-Medium",
        "expected_return": "5-12% monthly",
        "best_for": "Ranging markets, BTC/ETH sideway trends",
        "tags": ["grid", "volatility", "automated"],
    },
    {
        "name": "Momentum",
        "description": "Trend-following strategy that captures directional moves. Uses multi-timeframe indicators for entry/exit.",
        "stars": 3,
        "risk": "High",
        "expected_return": "20-40% (when trending)",
        "best_for": "Strong trends, altcoin seasons",
        "tags": ["momentum", "trend", "altcoins"],
    },
    {
        "name": "DEX Arbitrage (Solana)",
        "description": "Cross-Dex arbitrage on Solana ecosystem. Targets Raydium, Orca, and Phoenix price inefficiencies.",
        "stars": 5,
        "risk": "Medium",
        "expected_return": "12-20% monthly",
        "best_for": "Solana ecosystem, SPL tokens",
        "tags": ["solana", "arbitrage", "DEX"],
    },
    {
        "name": "LLM Enhanced (TradingAgents)",
        "description": "AI-powered strategy using multi-agent debate system. Combines on-chain data + sentiment analysis for adaptive decisions.",
        "stars": 5,
        "risk": "Medium (adaptive)",
        "expected_return": "Variable (market-aware)",
        "best_for": "Dynamic market conditions, all environments",
        "tags": ["AI", "LLM", "adaptive", "TradingAgents"],
    },
    {
        "name": "Hybrid (Multi-Strategy)",
        "description": "Combines multiple strategies (grid + momentum + arb) with dynamic allocation based on market regime detection.",
        "stars": 4,
        "risk": "Medium",
        "expected_return": "10-18% monthly",
        "best_for": "All market conditions, diversified exposure",
        "tags": ["hybrid", "multi-strategy", "regime-aware"],
    },
    {
        "name": "Autopilot (AI picks)",
        "description": "Fully autonomous mode where AI selects and switches strategies in real-time based on market conditions and performance.",
        "stars": 4,
        "risk": "Medium-High (delegated)",
        "expected_return": "Variable",
        "best_for": "Hands-off trading, AI-first approach",
        "tags": ["autopilot", "AI", "autonomous", "hands-off"],
    },
]


def render_stars(n: int) -> str:
    """Render star rating as emoji."""
    return "⭐" * n


def render_risk_badge(risk: str) -> str:
    """Render risk level as colored badge text."""
    risk_colors = {
        "Low": "🟢",
        "Low-Medium": "🟢🟡",
        "Medium": "🟡",
        "Medium-High": "🟡🟠",
        "High": "🟠",
        "Medium (adaptive)": "🟡🤖",
        "Medium-High (delegated)": "🟡🟠🤖",
    }
    return risk_colors.get(risk, "⚪")


def render_strategy_card(strategy: Dict[str, Any], index: int) -> None:
    """Render a single strategy card."""
    st.markdown(f"### {strategy['name']}")
    st.markdown(f"{render_stars(strategy['stars'])}")
    st.markdown(f"**Risk:** {render_risk_badge(strategy['risk'])} {strategy['risk']}")
    st.markdown(f"**Expected Return:** {strategy['expected_return']}")
    st.markdown(f"*{strategy['description']}*")
    st.markdown(f"**Best for:** {strategy['best_for']}")

    # Tags
    tag_str = " ".join([f"`{tag}`" for tag in strategy["tags"]])
    st.markdown(f"Tags: {tag_str}")

    # Select button
    is_selected = st.session_state.get("selected_strategy") == strategy["name"]
    label = "✅ Selected" if is_selected else "Select Strategy"
    if st.button(label, key=f"select_{index}"):
        st.session_state.selected_strategy = strategy["name"]
        st.rerun()

    st.markdown("---")


def render_llm_advisor_panel() -> None:
    """Render the LLM Strategy Advisor panel."""
    st.subheader("🤖 LLM Strategy Advisor")
    st.markdown(
        "Get AI-powered strategy recommendations using multi-agent debate "
        "(On-Chain Data Analyst + Sentiment Analyst → Strategy Selector)."
    )

    if LLMStrategyAdvisor is None:
        st.warning("LLM Advisor module not available. Check `llm_advisor.py`.")
        return

    provider = st.selectbox(
        "LLM Provider",
        options=["openai", "anthropic", "ollama"],
        index=0,
        help="Select the LLM provider for strategy recommendations"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### On-Chain Data (Mock)")
        onchain_score = st.slider("Market On-Chain Score", 0, 100, 65)
        st.write(f"**Score:** {onchain_score}/100")
        st.write(f"**Interpretation:** {'Bullish' if onchain_score > 60 else 'Neutral' if onchain_score > 40 else 'Bearish'}")

    with col2:
        st.markdown("#### Sentiment Data (Mock)")
        sentiment_score = st.slider("Market Sentiment Score", 0, 100, 55)
        st.write(f"**Score:** {sentiment_score}/100")
        st.write(f"**Interpretation:** {'Positive' if sentiment_score > 60 else 'Neutral' if sentiment_score > 40 else 'Negative'}")

    if st.button("🔮 Get LLM Recommendation"):
        with st.spinner("Running multi-agent debate..."):
            advisor = LLMStrategyAdvisor(provider=provider)
            result = advisor.get_recommendation(
                onchain_score=onchain_score,
                sentiment_score=sentiment_score
            )

            st.success("Recommendation received!")
            st.markdown("---")
            st.markdown("#### 📋 LLM Recommendation")
            st.markdown(f"**Recommended Strategy:** `{result['recommended_strategy']}`")
            st.markdown(f"**Confidence:** {result['confidence']}%")
            st.markdown(f"**Reasoning:**\n\n{result['reasoning']}")

            if result.get('debate_log'):
                st.markdown("---")
                st.markdown("#### 🗣️ Agent Debate Log")
                for entry in result['debate_log']:
                    st.markdown(f"**{entry['agent']}:** {entry['message']}")


def render_strategies() -> None:
    """Render the Strategies page."""
    st.title("🎯 Strategy Selector")
    st.markdown(
        "Choose a trading strategy for your agents. Each strategy has different "
        "risk/return profiles. Use the LLM Advisor for AI-powered recommendations."
    )
    st.markdown("---")

    # Currently selected strategy banner
    selected = st.session_state.get("selected_strategy", "None")
    st.info(f"**Currently Active Strategy:** {selected}")

    # LLM Advisor
    with st.expander("🤖 LLM Strategy Advisor (AI-powered recommendations)"):
        render_llm_advisor_panel()

    st.markdown("---")

    # Strategy cards - 2 column layout
    st.subheader("Available Strategies")

    cols = st.columns(2)
    for idx, strategy in enumerate(STRATEGIES):
        with cols[idx % 2]:
            render_strategy_card(strategy, idx)


if __name__ == "__main__":
    render_strategies()
