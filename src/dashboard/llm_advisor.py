"""
KEOTrading Dashboard - LLM Strategy Advisor
=============================================
Multi-agent debate system for AI-powered strategy recommendations.
Combines: On-Chain Data Analyst + Sentiment Analyst → Strategy Selector
"""

from __future__ import annotations

import json
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


# -------------------------------------------------------------------
# Strategy definitions (mirrors the strategies page)
# -------------------------------------------------------------------
STRATEGIES = [
    {"name": "LP Arbitrage (hzjken)", "risk": "Medium", "return": "15-25% APR", "best_for": "stable pairs"},
    {"name": "Scalping (Mean Reversion)", "risk": "Medium-High", "return": "8-15% monthly", "best_for": "high-liquidity pairs"},
    {"name": "Grid Trading", "risk": "Low-Medium", "return": "5-12% monthly", "best_for": "ranging markets"},
    {"name": "Momentum", "risk": "High", "return": "20-40%", "best_for": "strong trends"},
    {"name": "DEX Arbitrage (Solana)", "risk": "Medium", "return": "12-20% monthly", "best_for": "Solana ecosystem"},
    {"name": "LLM Enhanced (TradingAgents)", "risk": "Medium (adaptive)", "return": "Variable", "best_for": "dynamic conditions"},
    {"name": "Hybrid (Multi-Strategy)", "risk": "Medium", "return": "10-18% monthly", "best_for": "all conditions"},
    {"name": "Autopilot (AI picks)", "risk": "Medium-High (delegated)", "return": "Variable", "best_for": "hands-off"},
]


# -------------------------------------------------------------------
# Agent personas
# -------------------------------------------------------------------
@dataclass
class OnChainAnalyst:
    """Mock on-chain data analyst agent."""

    name: str = "On-Chain Data Analyst"
    persona: str = (
        "You analyze blockchain data: TVL, DEX volume, gas fees, "
        "token flows, LP depth, and protocol metrics to assess market health."
    )

    def analyze(self, onchain_score: int) -> Dict[str, Any]:
        """Return on-chain analysis based on score (0-100)."""
        if onchain_score >= 70:
            health = "BULLISH - Strong on-chain activity, high TVL growth"
            tvl_trend = "↑ +23% in 7 days"
            dex_vol = "↑ High DEX volume ($2.4B daily)"
            gas_status = "Moderate (avg 25 gwei)"
        elif onchain_score >= 40:
            health = "NEUTRAL - Average on-chain metrics"
            tvl_trend = "→ Stable TVL"
            dex_vol = "→ Normal DEX volume ($1.1B daily)"
            gas_status = "Low (avg 15 gwei)"
        else:
            health = "BEARISH - Weak on-chain signals, declining activity"
            tvl_trend = "↓ TVL contracting"
            dex_vol = "↓ Low DEX volume ($0.6B daily)"
            gas_status = "Very low (avg 8 gwei)"

        return {
            "health": health,
            "tvl_trend": tvl_trend,
            "dex_volume": dex_vol,
            "gas_status": gas_status,
            "score": onchain_score,
            "interpretation": (
                f"TVL {tvl_trend}, DEX volume {dex_vol}, Gas {gas_status}. "
                f"Overall assessment: {health.lower().replace('-', ':')}"
            ),
        }


@dataclass
class SentimentAnalyst:
    """Mock sentiment analyst agent."""

    name: str = "Sentiment Analyst"
    persona: str = (
        "You analyze market sentiment from social media, news, "
        "funding rates, option skew, and trader positioning data."
    )

    def analyze(self, sentiment_score: int) -> Dict[str, Any]:
        """Return sentiment analysis based on score (0-100)."""
        if sentiment_score >= 70:
            mood = "GREED / BULLISH - Risk appetite elevated"
            social = "Twitter trending: #crypto #bullish"
            funding = "Positive funding rates (+0.01%)"
            positioning = "Long-heavy positioning"
        elif sentiment_score >= 40:
            mood = "NEUTRAL - Cautious optimism"
            social = "Mixed sentiment on social channels"
            funding = "Neutral funding rates (0.00%)"
            positioning = "Balanced positioning"
        else:
            mood = "FEAR / BEARISH - Risk aversion elevated"
            social = "Negative bias in social channels"
            funding = "Negative funding rates (-0.02%)"
            positioning = "Short-heavy positioning"

        return {
            "mood": mood,
            "social_trends": social,
            "funding_rates": funding,
            "positioning": positioning,
            "score": sentiment_score,
            "interpretation": (
                f"Market mood: {mood}. {social}. "
                f"Funding: {funding}. Positioning: {positioning}."
            ),
        }


# -------------------------------------------------------------------
# Strategy Selector (LLM-driven)
# -------------------------------------------------------------------
class StrategySelector:
    """
    Mock LLM strategy selector using TradingAgents-style multi-agent debate.
    In production, this would call a real LLM API.
    """

    def __init__(self, provider: str = "openai", model: str = "gpt-4o"):
        self.provider = provider
        self.model = model
        self.onchain_analyst = OnChainAnalyst()
        self.sentiment_analyst = SentimentAnalyst()

    def _build_prompt(
        self,
        onchain: Dict[str, Any],
        sentiment: Dict[str, Any],
        available_strategies: List[Dict],
    ) -> str:
        """Build the debate prompt for strategy selection."""
        strat_list = "\n".join(
            f"- {s['name']}: risk={s['risk']}, return={s['return']}, best_for={s['best_for']}"
            for s in available_strategies
        )
        return f"""You are the Strategy Selector in a multi-agent trading debate system.

Context:
- On-Chain Analyst says: {onchain['interpretation']}
- Sentiment Analyst says: {sentiment['interpretation']}

Available strategies:
{strat_list}

Task: Select the best strategy and provide a confidence score (0-100).

Respond with JSON:
{{"strategy": "strategy name", "confidence": 0-100, "reasoning": "why this strategy"}}
"""

    def select(
        self,
        onchain_score: int,
        sentiment_score: int,
        risk_tolerance: str = "medium",
    ) -> Dict[str, Any]:
        """Run the mock debate and return a strategy recommendation."""
        onchain = self.onchain_analyst.analyze(onchain_score)
        sentiment = self.sentiment_analyst.analyze(sentiment_score)

        # Build mock LLM response
        prompt = self._build_prompt(onchain, sentiment, STRATEGIES)

        # Determine strategy based on signals (mock LLM logic)
        if onchain_score >= 60 and sentiment_score >= 60:
            # Bullish market → momentum / LLM Enhanced
            if onchain_score > 75:
                strategy = "Momentum"
                confidence = min(95, 60 + (onchain_score - 60) // 2 + (sentiment_score - 60) // 2)
            else:
                strategy = "LLM Enhanced (TradingAgents)"
                confidence = min(90, 55 + (onchain_score - 40) // 3 + (sentiment_score - 40) // 3)
        elif onchain_score >= 50 and sentiment_score < 40:
            # High on-chain but fearful → grid / arbitrage
            strategy = random.choice(["Grid Trading", "LP Arbitrage (hzjken)"])
            confidence = 65 + (onchain_score - 50) // 3
        elif onchain_score < 40 and sentiment_score < 40:
            # Bearish → defensive strategies
            strategy = "Grid Trading"
            confidence = 70
        elif onchain_score >= 60 and sentiment_score < 40:
            # On-chain strong but sentiment weak → hybrid / autopilot
            strategy = "Hybrid (Multi-Strategy)"
            confidence = 72
        else:
            # Neutral → balanced / hybrid
            strategy = "Hybrid (Multi-Strategy)"
            confidence = 60

        confidence = min(95, max(40, confidence))

        return {
            "strategy": strategy,
            "confidence": confidence,
            "reasoning": (
                f"On-chain score ({onchain_score}/100): {onchain['health']}. "
                f"Sentiment ({sentiment_score}/100): {sentiment['mood']}. "
                f"Selected '{strategy}' as optimal for current conditions. "
                f"Confidence: {confidence}%."
            ),
            "onchain_analysis": onchain,
            "sentiment_analysis": sentiment,
        }


# -------------------------------------------------------------------
# Main Advisor Class
# -------------------------------------------------------------------
class LLMStrategyAdvisor:
    """
    High-level LLM Strategy Advisor using TradingAgents-style multi-agent debate.

    Pipeline:
    1. On-Chain Analyst gathers blockchain metrics
    2. Sentiment Analyst gathers market mood data
    3. Strategy Selector (LLM) debates and picks best strategy
    4. Returns recommendation with confidence score
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.selector = StrategySelector(provider=provider, model=model)

    def get_recommendation(
        self,
        onchain_score: int = 65,
        sentiment_score: int = 55,
        risk_tolerance: str = "medium",
    ) -> Dict[str, Any]:
        """
        Get a strategy recommendation from the multi-agent debate system.

        Args:
            onchain_score: On-chain health score (0-100)
            sentiment_score: Market sentiment score (0-100)
            risk_tolerance: Risk tolerance (low, medium, high)

        Returns:
            Dict with recommended_strategy, confidence, reasoning, and debate_log
        """
        result = self.selector.select(
            onchain_score=onchain_score,
            sentiment_score=sentiment_score,
            risk_tolerance=risk_tolerance,
        )

        # Build debate log
        debate_log = [
            {
                "agent": "On-Chain Data Analyst",
                "message": result["onchain_analysis"]["interpretation"],
            },
            {
                "agent": "Sentiment Analyst",
                "message": result["sentiment_analysis"]["interpretation"],
            },
            {
                "agent": "Strategy Selector (LLM)",
                "message": f"Selected {result['strategy']} with {result['confidence']}% confidence. {result['reasoning']}",
            },
        ]

        return {
            "recommended_strategy": result["strategy"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "debate_log": debate_log,
            "provider": self.provider,
            "model": self.model,
        }


# -------------------------------------------------------------------
# Convenience function for Streamlit integration
# -------------------------------------------------------------------
def get_advisor(provider: str = "openai") -> LLMStrategyAdvisor:
    """Factory function to create an LLM advisor instance."""
    return LLMStrategyAdvisor(provider=provider)
