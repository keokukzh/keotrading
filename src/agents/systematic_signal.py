"""
Systematic Signal Generator
Combines On-Chain, Macro, and Sentiment into a unified trading signal.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from src.agents.onchain_regime import (
    OnChainRegimeDetector, 
    MarketRegime, 
    RegimeSignal as OnChainSignal
)
from src.agents.macro_regime import (
    MacroRegimeDetector, 
    MacroRegime, 
    MacroSignal
)
from src.agents.sentiment_detector import (
    SentimentDetector, 
    SentimentLevel, 
    SentimentSignal
)

logger = logging.getLogger(__name__)


@dataclass
class LayerScore:
    """Score for a single regime layer."""
    layer_name: str
    score: int           # -1, 0, or +1
    value: str           # Human-readable value
    details: str         # Detailed explanation
    is_extreme: bool     # Is at extreme (stronger signal)
    
    @property
    def label(self) -> str:
        if self.score == 1:
            return "🟢 BULLISH"
        elif self.score == -1:
            return "🔴 BEARISH"
        return "🟡 NEUTRAL"


@dataclass
class UnifiedSignal:
    """Unified trading signal from all 3 layers."""
    timestamp: datetime
    
    # Individual layer scores
    onchain_score: LayerScore
    macro_score: LayerScore
    sentiment_score: LayerScore
    
    # Combined score
    total_score: int        # -3 to +3
    confidence: float       # 0.0 to 1.0
    
    # Trading signal
    action: str             # "ACCUMULATE", "HOLD", "REDUCE"
    position_change: float  # % change per week
    conviction: str        # "HIGH", "MEDIUM", "LOW"
    
    # Historical stats
    historical_return: float  # Expected return at this score
    hit_rate: float           # % of time signal was correct
    sample_size: int          # Number of occurrences
    
    # All data
    onchain_signal: OnChainSignal
    macro_signal: MacroSignal
    sentiment_signal: SentimentSignal
    
    # Interpretation
    interpretation: str
    warnings: List[str] = field(default_factory=list)
    
    def __str__(self):
        emoji = "🟢" if self.total_score >= 2 else "🔴" if self.total_score <= -2 else "🟡"
        return f"{emoji} Score: {self.total_score}/3 ({self.action})"


class ScoringRules:
    """Defines scoring and trading rules."""
    
    # Score boundaries
    ACCUMULATE_THRESHOLD = 2   # Score >= +2
    REDUCE_THRESHOLD = -2      # Score <= -2
    
    # Position change (% per week)
    ACCUMULATE_POSITION_CHANGE = 2.0   # Add 2% per week
    REDUCE_POSITION_CHANGE = -2.0       # Trim 2% per week
    
    # Historical returns by score level (mock data based on backtesting)
    HISTORICAL_STATS = {
        # Score: (expected_return_30d, hit_rate, sample_size)
        3: (0.18, 0.82, 45),     # Strong bullish
        2: (0.12, 0.74, 120),    # Bullish
        1: (0.04, 0.56, 200),    # Slightly bullish
        0: (0.00, 0.50, 350),     # Neutral
        -1: (-0.03, 0.52, 180),   # Slightly bearish
        -2: (-0.10, 0.69, 110),   # Bearish
        -3: (-0.16, 0.78, 40),    # Strong bearish
    }


class SystematicSignalGenerator:
    """
    Combines On-Chain, Macro, and Sentiment into unified signal.
    
    Scoring System:
    - Each layer: +1 (bullish), 0 (neutral), -1 (bearish)
    - Total: -3 to +3
    
    Trading Rules:
    - Score >= +2 → ACCUMULATE (add 2% per week)
    - Score -1 to +1 → HOLD (no action)
    - Score <= -2 → REDUCE (trim 2% per week)
    """
    
    def __init__(
        self,
        onchain_detector: OnChainRegimeDetector = None,
        macro_detector: MacroRegimeDetector = None,
        sentiment_detector: SentimentDetector = None
    ):
        self.onchain = onchain_detector or OnChainRegimeDetector()
        self.macro = macro_detector or MacroRegimeDetector()
        self.sentiment = sentiment_detector or SentimentDetector()
        self.rules = ScoringRules()
        
        self._last_signal: Optional[UnifiedSignal] = None
    
    async def generate_signal(self, use_cache: bool = False) -> UnifiedSignal:
        """Generate unified signal from all 3 layers."""
        
        if use_cache and self._last_signal:
            age = (datetime.now() - self._last_signal.timestamp).total_seconds()
            if age < 300:  # 5 minutes
                return self._last_signal
        
        # Fetch all layer signals
        onchain_signal = await self.onchain.get_regime_signal(use_cache)
        macro_signal = await self.macro.get_macro_signal(use_cache)
        sentiment_signal = await self.sentiment.get_sentiment_signal(use_cache)
        
        # Score each layer
        onchain_score = self._score_onchain(onchain_signal)
        macro_score = self._score_macro(macro_signal)
        sentiment_score = self._score_sentiment(sentiment_signal)
        
        # Calculate total
        total = onchain_score.score + macro_score.score + sentiment_score.score
        
        # Determine action
        action, position_change, conviction = self._determine_action(total)
        
        # Get historical stats
        historical_return, hit_rate, sample_size = self._get_historical_stats(total)
        
        # Generate interpretation
        interpretation = self._generate_interpretation(
            total, onchain_score, macro_score, sentiment_score, action
        )
        
        # Check for warnings
        warnings = self._check_warnings(
            onchain_score, macro_score, sentiment_score
        )
        
        self._last_signal = UnifiedSignal(
            timestamp=datetime.now(),
            onchain_score=onchain_score,
            macro_score=macro_score,
            sentiment_score=sentiment_score,
            total_score=total,
            confidence=abs(total) / 3,
            action=action,
            position_change=position_change,
            conviction=conviction,
            historical_return=historical_return,
            hit_rate=hit_rate,
            sample_size=sample_size,
            onchain_signal=onchain_signal,
            macro_signal=macro_signal,
            sentiment_signal=sentiment_signal,
            interpretation=interpretation,
            warnings=warnings
        )
        
        return self._last_signal
    
    def _score_onchain(self, signal: OnChainSignal) -> LayerScore:
        """Score on-chain regime."""
        
        if signal.regime == MarketRegime.ACCUMULATION:
            score = 1
            value = "Accumulation"
            details = f"Smart money accumulating. Expected 30d return: +{signal.forward_return_30d:.0%}"
            is_extreme = signal.confidence > 0.8
        elif signal.regime == MarketRegime.DISTRIBUTION:
            score = -1
            value = "Distribution"
            details = f"Smart money distributing. Expected 30d return: {signal.forward_return_30d:.0%}"
            is_extreme = signal.confidence > 0.8
        else:  # TRANSITION or UNKNOWN
            score = 0
            value = "Transition"
            details = "Mixed signals. Awaiting clarity."
            is_extreme = False
        
        return LayerScore(
            layer_name="On-Chain",
            score=score,
            value=value,
            details=details,
            is_extreme=is_extreme
        )
    
    def _score_macro(self, signal: MacroSignal) -> LayerScore:
        """Score macro regime."""
        
        if signal.regime == MacroRegime.CRYPTO_TAILWIND:
            score = 1
            value = "Crypto Tailwind"
            details = "Weak dollar, falling yields, rising M2 = bullish"
            is_extreme = signal.confidence > 0.8
        elif signal.regime == MacroRegime.CRYPTO_HEADWIND:
            score = -1
            value = "Crypto Headwind"
            details = "Strong dollar, rising yields, falling M2 = bearish"
            is_extreme = signal.confidence > 0.8
        else:  # NEUTRAL
            score = 0
            value = "Neutral"
            details = "Mixed macro conditions."
            is_extreme = False
        
        return LayerScore(
            layer_name="Macro",
            score=score,
            value=value,
            details=details,
            is_extreme=is_extreme
        )
    
    def _score_sentiment(self, signal: SentimentSignal) -> LayerScore:
        """Score sentiment."""
        
        if signal.level == SentimentLevel.EXTREME_FEAR:
            # Extreme fear is BULLISH (contrarian)
            score = 1
            value = "Extreme Fear"
            details = f"Contrarian BUY signal. {signal.historical_accuracy:.0%} historical bounce rate."
            is_extreme = True
        elif signal.level == SentimentLevel.FEAR:
            score = 0
            value = "Fear"
            details = "Some fear present but not extreme."
            is_extreme = False
        elif signal.level == SentimentLevel.EXTREME_GREED:
            # Extreme greed is BEARISH (contrarian)
            score = -1
            value = "Extreme Greed"
            details = f"Contrarian SELL signal. {signal.historical_accuracy:.0%}% pullback probability."
            is_extreme = True
        elif signal.level == SentimentLevel.GREED:
            score = 0
            value = "Greed"
            details = "Some greed building but not extreme."
            is_extreme = False
        else:  # NEUTRAL
            score = 0
            value = "Neutral"
            details = "Sentiment balanced."
            is_extreme = False
        
        return LayerScore(
            layer_name="Sentiment",
            score=score,
            value=value,
            details=details,
            is_extreme=is_extreme
        )
    
    def _determine_action(self, total_score: int) -> Tuple[str, float, str]:
        """Determine trading action from total score."""
        
        if total_score >= self.rules.ACCUMULATE_THRESHOLD:
            action = "ACCUMULATE"
            position_change = self.rules.ACCUMULATE_POSITION_CHANGE
            
            if total_score == 3:
                conviction = "HIGH"
            else:
                conviction = "MEDIUM"
                
        elif total_score <= self.rules.REDUCE_THRESHOLD:
            action = "REDUCE"
            position_change = self.rules.REDUCE_POSITION_CHANGE
            
            if total_score == -3:
                conviction = "HIGH"
            else:
                conviction = "MEDIUM"
        else:
            action = "HOLD"
            position_change = 0.0
            conviction = "LOW"
        
        return action, position_change, conviction
    
    def _get_historical_stats(self, score: int) -> Tuple[float, float, int]:
        """Get historical stats for a score level."""
        score = max(-3, min(3, score))  # Clamp
        stats = self.rules.HISTORICAL_STATS.get(score, (0.0, 0.5, 0))
        return stats
    
    def _generate_interpretation(
        self,
        total: int,
        onchain: LayerScore,
        macro: LayerScore,
        sentiment: LayerScore,
        action: str
    ) -> str:
        """Generate human-readable interpretation."""
        
        if total >= 2:
            base = f"🟢 **STRONG BULLISH SIGNAL** (Score: {total}/3)\n\n"
            base += "All layers align for bullish outlook:\n"
            
            if onchain.score == 1:
                base += f"• {onchain.value}: {onchain.details}\n"
            if macro.score == 1:
                base += f"• {macro.value}: {macro.details}\n"
            if sentiment.score == 1:
                base += f"• {sentiment.value}: {sentiment.details}\n"
            
            base += f"\n→ {action} Bitcoin position (+2%/week)"
            
        elif total <= -2:
            base = f"🔴 **STRONG BEARISH SIGNAL** (Score: {total}/3)\n\n"
            base += "All layers align for bearish outlook:\n"
            
            if onchain.score == -1:
                base += f"• {onchain.value}: {onchain.details}\n"
            if macro.score == -1:
                base += f"• {macro.value}: {macro.details}\n"
            if sentiment.score == -1:
                base += f"• {sentiment.value}: {sentiment.details}\n"
            
            base += f"\n→ {action} Bitcoin position (-2%/week)"
            
        elif total == 1:
            base = f"🟡 **SLIGHTLY BULLISH** (Score: {total}/3)\n\n"
            base += "Mild bullish bias:\n"
            for layer in [onchain, macro, sentiment]:
                if layer.score == 1:
                    base += f"• {layer.value}: {layer.details}\n"
            
            base += f"\n→ {action} - no strong conviction"
            
        elif total == -1:
            base = f"🟡 **SLIGHTLY BEARISH** (Score: {total}/3)\n\n"
            base += "Mild bearish bias:\n"
            for layer in [onchain, macro, sentiment]:
                if layer.score == -1:
                    base += f"• {layer.value}: {layer.details}\n"
            
            base += f"\n→ {action} - no strong conviction"
            
        else:
            base = f"⚪ **NEUTRAL** (Score: {total}/3)\n\n"
            base += "Mixed signals across layers:\n"
            
            for layer in [onchain, macro, sentiment]:
                base += f"• {layer.layer_name}: {layer.value}\n"
            
            base += f"\n→ {action} - await clearer signals"
        
        return base
    
    def _check_warnings(
        self,
        onchain: LayerScore,
        macro: LayerScore,
        sentiment: LayerScore
    ) -> List[str]:
        """Check for warning conditions."""
        warnings = []
        
        # Check for contradictions
        scores = [onchain.score, macro.score, sentiment.score]
        if max(scores) == 1 and min(scores) == -1:
            warnings.append("⚠️ Layer disagreement - signals are mixed across regimes")
        
        # Check for extreme sentiment alone
        if sentiment.is_extreme and onchain.score == 0 and macro.score == 0:
            warnings.append("⚠️ Sentiment is extreme but fundamentals neutral - await confirmation")
        
        # Check for low confidence
        if onchain.is_extreme == False and macro.is_extreme == False and sentiment.is_extreme == False:
            if abs(sum(scores)) < 2:
                warnings.append("⚠️ No extreme signals - await stronger conviction")
        
        return warnings
    
    def get_signal(self, use_cache: bool = False) -> UnifiedSignal:
        """Get cached signal (synchronous)."""
        if use_cache and self._last_signal:
            return self._last_signal
        raise ValueError("Call generate_signal() first (async)")
