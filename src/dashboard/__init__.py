"""
KEOTrading Dashboard Module
===========================
Streamlit dashboard + FastAPI backend for multi-agent crypto trading.
"""

from __future__ import annotations

from src.dashboard.llm_advisor import (
    LLMStrategyAdvisor,
    OnChainAnalyst,
    SentimentAnalyst,
    StrategySelector,
    get_advisor,
)

__all__ = [
    "LLMStrategyAdvisor",
    "OnChainAnalyst",
    "SentimentAnalyst",
    "StrategySelector",
    "get_advisor",
]
