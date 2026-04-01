"""
Macro Regime Detector
Analyzes macroeconomic indicators from FRED to classify market conditions.
Supports DXY, 10-Year Yield, VIX, and M2 Money Supply.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class MacroRegime(Enum):
    """Macro regime classification."""
    CRYPTO_TAILWIND = "crypto_tailwind"   # Weak dollar, falling yields, rising M2
    CRYPTO_HEADWIND = "crypto_headwind"   # Strong dollar, rising yields, falling M2
    NEUTRAL = "neutral"                  # Mixed signals
    UNKNOWN = "unknown"


@dataclass
class MacroMetrics:
    """Container for macro economic indicators."""
    dxy_current: float = 0.0
    dxy_change_30d: float = 0.0
    dxy_trend: str = "neutral"
    
    yield_10y_current: float = 0.0
    yield_10y_change_30d: float = 0.0
    yield_trend: str = "neutral"
    
    vix_current: float = 0.0
    vix_change_30d: float = 0.0
    vix_trend: str = "neutral"
    
    m2_current: float = 0.0
    m2_change_30d: float = 0.0
    m2_change_yoy: float = 0.0
    m2_trend: str = "neutral"
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MacroSignal:
    """Result of macro regime classification."""
    regime: MacroRegime
    confidence: float
    alignment_score: float
    indicators: Dict[str, float]
    regime_scores: Dict[MacroRegime, float]
    interpretation: str
    tailwind_reasons: List[str] = field(default_factory=list)
    headwind_reasons: List[str] = field(default_factory=list)
    
    onchain_regime: str = ""
    onchain_regime_match: bool = False
    confirmation_signal: str = ""
    
    def __str__(self):
        emoji = {
            MacroRegime.CRYPTO_TAILWIND: "🟢",
            MacroRegime.CRYPTO_HEADWIND: "🔴",
            MacroRegime.NEUTRAL: "🟡",
            MacroRegime.UNKNOWN: "⚪"
        }.get(self.regime, "⚪")
        return f"{emoji} {self.regime.value.upper()} ({self.confidence:.0%} confidence)"


class MockMacroProvider:
    """Generate realistic mock macro data."""
    
    async def fetch_all(self) -> MacroMetrics:
        """Generate realistic mock macro metrics."""
        import random
        
        cycle_phase = random.choice(['early_bull', 'late_bull', 'early_bear', 'late_bear'])
        
        if cycle_phase == 'early_bull':
            dxy = random.uniform(98, 102)
            dxy_change = random.uniform(-3, -1)
            yield_10y = random.uniform(3.5, 4.5)
            yield_change = random.uniform(-5, -2)
            vix = random.uniform(12, 18)
            vix_change = random.uniform(-20, -5)
            m2 = random.uniform(20, 21)
            m2_change = random.uniform(0.3, 0.8)
            
        elif cycle_phase == 'late_bull':
            dxy = random.uniform(102, 106)
            dxy_change = random.uniform(1, 3)
            yield_10y = random.uniform(4.5, 5.5)
            yield_change = random.uniform(3, 8)
            vix = random.uniform(15, 22)
            vix_change = random.uniform(-10, 20)
            m2 = random.uniform(20.5, 21)
            m2_change = random.uniform(0.1, 0.4)
            
        elif cycle_phase == 'early_bear':
            dxy = random.uniform(106, 112)
            dxy_change = random.uniform(2, 5)
            yield_10y = random.uniform(4.5, 5.5)
            yield_change = random.uniform(-2, 2)
            vix = random.uniform(25, 40)
            vix_change = random.uniform(20, 60)
            m2 = random.uniform(19.5, 20.5)
            m2_change = random.uniform(-0.5, 0.1)
            
        else:
            dxy = random.uniform(100, 104)
            dxy_change = random.uniform(-2, 0)
            yield_10y = random.uniform(3.0, 4.0)
            yield_change = random.uniform(-8, -3)
            vix = random.uniform(18, 28)
            vix_change = random.uniform(-30, 10)
            m2 = random.uniform(20, 21)
            m2_change = random.uniform(0.4, 1.0)
        
        return MacroMetrics(
            dxy_current=dxy,
            dxy_change_30d=dxy_change,
            dxy_trend="strong" if dxy_change > 1 else "weak" if dxy_change < -1 else "neutral",
            yield_10y_current=yield_10y,
            yield_10y_change_30d=yield_change,
            yield_trend="rising" if yield_change > 2 else "falling" if yield_change < -2 else "neutral",
            vix_current=vix,
            vix_change_30d=vix_change,
            vix_trend="high_vol" if vix > 25 else "low_vol" if vix < 15 else "neutral",
            m2_current=m2,
            m2_change_30d=m2_change,
            m2_change_yoy=random.uniform(2, 6),
            m2_trend="expanding" if m2_change > 0.2 else "contracting" if m2_change < 0 else "neutral",
            timestamp=datetime.now()
        )


class MacroClassifier:
    """Classifies macro regime from indicators."""
    
    def __init__(self):
        self.weights = {
            'dxy': {MacroRegime.CRYPTO_TAILWIND: -0.3, MacroRegime.CRYPTO_HEADWIND: 0.3},
            'yield': {MacroRegime.CRYPTO_TAILWIND: -0.25, MacroRegime.CRYPTO_HEADWIND: 0.25},
            'vix': {MacroRegime.CRYPTO_TAILWIND: -0.15, MacroRegime.CRYPTO_HEADWIND: 0.15},
            'm2': {MacroRegime.CRYPTO_TAILWIND: 0.3, MacroRegime.CRYPTO_HEADWIND: -0.3},
        }
    
    def classify(self, metrics: MacroMetrics) -> MacroSignal:
        """Classify macro regime from metrics."""
        
        indicators = {
            'dxy': max(-1, min(1, metrics.dxy_change_30d / 3)),
            'yield': max(-1, min(1, metrics.yield_10y_change_30d / 5)),
            'vix': self._normalize_vix(metrics.vix_current, metrics.vix_change_30d),
            'm2': max(-1, min(1, metrics.m2_change_30d / 1)),
        }
        
        regime_scores = {regime: 0.0 for regime in MacroRegime}
        
        for indicator, value in indicators.items():
            if indicator in self.weights:
                for regime, weight in self.weights[indicator].items():
                    regime_scores[regime] += weight * value
        
        alignment_score = regime_scores[MacroRegime.CRYPTO_HEADWIND] - regime_scores[MacroRegime.CRYPTO_TAILWIND]
        
        max_regime = MacroRegime.NEUTRAL
        max_score = 0
        
        for regime, score in regime_scores.items():
            if abs(score) > abs(max_score):
                max_score = score
                max_regime = regime if abs(score) > 0.1 else MacroRegime.NEUTRAL
        
        confidence = min(0.95, abs(max_score) / 0.4)
        
        tailwind, headwind = self._generate_reasons(metrics)
        interpretation = self._generate_interpretation(metrics, max_regime)
        
        return MacroSignal(
            regime=max_regime,
            confidence=confidence,
            alignment_score=alignment_score,
            indicators=indicators,
            regime_scores=regime_scores,
            interpretation=interpretation,
            tailwind_reasons=tailwind,
            headwind_reasons=headwind
        )
    
    def _normalize_vix(self, vix: float, change_30d: float) -> float:
        """Normalize VIX."""
        level = 1 if vix > 30 else 0.5 if vix > 20 else -1 if vix < 15 else -0.5 if vix < 18 else 0
        trend = max(-1, min(1, change_30d / 30))
        return (level + trend) / 2
    
    def _generate_reasons(self, m: MacroMetrics) -> Tuple[List[str], List[str]]:
        """Generate reasons."""
        tailwind, headwind = [], []
        
        if m.dxy_change_30d < -2:
            tailwind.append(f"Weak USD (DXY {m.dxy_change_30d:+.1f}%)")
        elif m.dxy_change_30d > 2:
            headwind.append(f"Strong USD (DXY {m.dxy_change_30d:+.1f}%)")
        
        if m.yield_10y_change_30d < -3:
            tailwind.append(f"Falling yields (10Y {m.yield_10y_change_30d:+.1f}%)")
        elif m.yield_10y_change_30d > 3:
            headwind.append(f"Rising yields (10Y {m.yield_10y_change_30d:+.1f}%)")
        
        if m.vix_current < 15:
            tailwind.append(f"Low volatility (VIX {m.vix_current:.1f})")
        elif m.vix_current > 25:
            headwind.append(f"High volatility (VIX {m.vix_current:.1f})")
        
        if m.m2_change_30d > 0.3:
            tailwind.append(f"Expanding M2 ({m.m2_change_30d:+.1f}%)")
        elif m.m2_change_30d < -0.2:
            headwind.append(f"Contracting M2 ({m.m2_change_30d:+.1f}%)")
        
        return tailwind, headwind
    
    def _generate_interpretation(self, m: MacroMetrics, regime: MacroRegime) -> str:
        """Generate interpretation."""
        if regime == MacroRegime.CRYPTO_TAILWIND:
            return "Macro conditions are FAVORABLE for crypto risk assets."
        elif regime == MacroRegime.CRYPTO_HEADWIND:
            return "Macro conditions are UNFAVORABLE for crypto risk assets."
        elif regime == MacroRegime.NEUTRAL:
            return "Macro conditions are MIXED for crypto."
        return "Unable to determine macro regime."
    
    def cross_check_onchain(self, macro_signal: MacroSignal, onchain_regime: str) -> MacroSignal:
        """Cross-check macro with on-chain regime."""
        macro_signal.onchain_regime = onchain_regime
        
        aligned_pairs = [
            (MacroRegime.CRYPTO_TAILWIND, "accumulation"),
            (MacroRegime.CRYPTO_HEADWIND, "distribution"),
            (MacroRegime.NEUTRAL, "transition"),
        ]
        
        onchain_lower = onchain_regime.lower()
        
        for macro_reg, onchain_key in aligned_pairs:
            if onchain_key in onchain_lower and macro_reg == macro_signal.regime:
                macro_signal.onchain_regime_match = True
                macro_signal.confirmation_signal = "CONFIRMED"
                macro_signal.interpretation += f" On-chain ({onchain_regime}) CONFIRMS macro view."
                return macro_signal
        
        if not macro_signal.onchain_regime_match:
            if "accumulation" in onchain_lower and macro_signal.regime == MacroRegime.CRYPTO_HEADWIND:
                macro_signal.confirmation_signal = "CONTRADICTED"
                macro_signal.interpretation += " WARNING: On-chain accumulation but macro headwinds!"
            elif "distribution" in onchain_lower and macro_signal.regime == MacroRegime.CRYPTO_TAILWIND:
                macro_signal.confirmation_signal = "CONTRADICTED"
                macro_signal.interpretation += " WARNING: On-chain distribution but macro tailwinds!"
            else:
                macro_signal.confirmation_signal = "NEUTRAL"
                macro_signal.interpretation += f" On-chain ({onchain_regime}) does not confirm/contradict."
        
        return macro_signal


class MacroRegimeDetector:
    """Main class for macro regime detection."""
    
    def __init__(self, provider=None):
        self.provider = provider or MockMacroProvider()
        self.classifier = MacroClassifier()
        self._last_signal: Optional[MacroSignal] = None
        self._last_metrics: Optional[MacroMetrics] = None
    
    async def get_macro_signal(self, use_cache: bool = False) -> MacroSignal:
        """Get current macro signal."""
        if use_cache and self._last_signal:
            age = (datetime.now() - self._last_metrics.timestamp).total_seconds()
            if age < 300:
                return self._last_signal
        
        self._last_metrics = await self.provider.fetch_all()
        self._last_signal = self.classifier.classify(self._last_metrics)
        return self._last_signal
    
    async def get_metrics(self) -> MacroMetrics:
        """Get raw macro metrics."""
        if not self._last_metrics:
            self._last_metrics = await self.provider.fetch_all()
        return self._last_metrics
    
    def analyze_alignment(self, onchain_regime: str) -> MacroSignal:
        """Get macro signal and cross-check with on-chain."""
        if not self._last_signal:
            return MacroSignal(
                regime=MacroRegime.UNKNOWN,
                confidence=0,
                alignment_score=0,
                indicators={},
                regime_scores={},
                interpretation="No data available"
            )
        return self.classifier.cross_check_onchain(self._last_signal, onchain_regime)
    
    def get_trade_recommendation(self, signal: MacroSignal) -> Dict[str, Any]:
        """Get trading recommendations based on macro regime."""
        recommendations = {
            MacroRegime.CRYPTO_TAILWIND: {
                "bias": "bullish", "leverage": "2-3x", "position_size": "increased",
                "hedging": "minimal", "stop_loss": "wider", "take_profit": "extended",
                "notes": "Favorable macro = higher beta strategies work"
            },
            MacroRegime.CRYPTO_HEADWIND: {
                "bias": "bearish", "leverage": "1-1.5x", "position_size": "reduced",
                "hedging": "required", "stop_loss": "tight", "take_profit": "earlier",
                "notes": "Headwinds = lower beta, focus on defensive"
            },
            MacroRegime.NEUTRAL: {
                "bias": "neutral", "leverage": "1-2x", "position_size": "normal",
                "hedging": "moderate", "stop_loss": "normal", "take_profit": "normal",
                "notes": "Mixed = await clarity"
            },
            MacroRegime.UNKNOWN: {
                "bias": "cautious", "leverage": "1x", "position_size": "minimal",
                "hedging": "full", "stop_loss": "very_tight", "take_profit": "quick",
                "notes": "No macro clarity = stay defensive"
            }
        }
        return recommendations.get(signal.regime, recommendations[MacroRegime.UNKNOWN])
