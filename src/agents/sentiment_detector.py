"""
Sentiment Detector
Analyzes market sentiment from Fear & Greed Index and LunarCrush social metrics.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import requests

logger = logging.getLogger(__name__)


class SentimentLevel(Enum):
    """Sentiment classification."""
    EXTREME_FEAR = "extreme_fear"   # F&G < 25
    FEAR = "fear"                    # F&G 25-45
    NEUTRAL = "neutral"             # F&G 45-55
    GREED = "greed"                 # F&G 55-75
    EXTREME_GREED = "extreme_greed" # F&G > 75
    UNKNOWN = "unknown"


@dataclass
class SentimentMetrics:
    """Container for sentiment indicators."""
    # Fear & Greed Index
    fng_value: int = 50              # 0-100
    fng_classification: str = "neutral"
    fng_change_24h: int = 0
    
    # LunarCrush Social Metrics
    social_volume: int = 0           # Social mentions
    social_engagement: float = 0.0    # Engagement score
    sentiment_score: float = 0.0      # -1 to 1
    sentiment_trend: str = "neutral"  # "rising", "falling"
    
    # Bitcoin-specific
    btc_dominant: bool = True
    bullish_ratio: float = 0.5        # % bullish posts
    
    # Additional
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SentimentSignal:
    """Result of sentiment analysis."""
    level: SentimentLevel
    value: int                          # F&G value (0-100)
    confidence: float
    is_extreme: bool
    extreme_type: str                   # "fear" or "greed" or ""
    buy_signal: bool                   # Extreme fear = buy signal
    historical_accuracy: float          # 76% for fear, 68% for greed
    
    # Contrarian analysis
    contrarian_signal: str              # "BUY" (fear), "SELL" (greed), "HOLD"
    contrarian_strength: float          # 0.0 to 1.0
    
    # Cross-regime alignment
    onchain_regime: str = ""
    macro_regime: str = ""
    alignment_with_fundamentals: bool = False
    confirmation_signal: str = ""      # "CONFIRMED", "CONTRADICTED", "NEUTRAL"
    
    interpretation: str = ""
    
    def __str__(self):
        emoji = {
            SentimentLevel.EXTREME_FEAR: "😱",
            SentimentLevel.FEAR: "😰",
            SentimentLevel.NEUTRAL: "😐",
            SentimentLevel.GREED: "🤑",
            SentimentLevel.EXTREME_GREED: "🤪",
        }.get(self.level, "❓")
        
        return f"{emoji} {self.value} - {self.level.value} ({self.confidence:.0%})"


class FearGreedProvider:
    """Alternative.me Fear & Greed Index API."""
    
    BASE_URL = "https://api.alternative.me/fng/"
    
    async def fetch(self) -> Tuple[int, str, int]:
        """
        Fetch current Fear & Greed index.
        Returns: (value, classification, change_24h)
        """
        try:
            response = requests.get(self.BASE_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    latest = data['data'][0]
                    value = int(latest.get('value', 50))
                    classification = latest.get('value_classification', 'neutral')
                    
                    # Get 24h change
                    if len(data['data']) > 1:
                        prev_value = int(data['data'][1].get('value', value))
                        change = value - prev_value
                    else:
                        change = 0
                    
                    return value, classification, change
        except Exception as e:
            logger.error(f"Fear & Greed API error: {e}")
        
        return 50, "neutral", 0


class LunarCrushProvider:
    """LunarCrush Social Metrics API."""
    
    BASE_URL = "https://lunarcrush.com/api"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('LUNARCRUSH_API_KEY', 'demo')
    
    async def fetch_btc_sentiment(self) -> SentimentMetrics:
        """Fetch Bitcoin social sentiment."""
        try:
            # Using free endpoint
            url = f"{self.BASE_URL}/coins/btc"
            params = {
                'key': self.api_key,
                'data': 'social'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    coin_data = data['data'][0]
                    
                    return SentimentMetrics(
                        social_volume=coin_data.get('social_volume', 0),
                        social_engagement=coin_data.get('social_engagement_total', 0),
                        sentiment_score=self._calc_sentiment(coin_data),
                        bullish_ratio=coin_data.get('bullish_sentiment', 0.5),
                        timestamp=datetime.now()
                    )
        except Exception as e:
            logger.error(f"LunarCrush API error: {e}")
        
        return SentimentMetrics()
    
    def _calc_sentiment(self, data: Dict) -> float:
        """Calculate sentiment score from LunarCrush data."""
        bullish = data.get('bullish_sentiment', 0.5)
        bearish = data.get('bearish_sentiment', 0.5)
        
        if bullish + bearish > 0:
            return (bullish - bearish) / (bullish + bearish)
        return 0.0


class MockSentimentProvider:
    """Generate realistic mock sentiment data."""
    
    async def fetch_fng(self) -> Tuple[int, str, int]:
        """Generate mock Fear & Greed."""
        import random
        
        # Simulate market cycle
        phase = random.choice(['fear', 'greed', 'extreme_fear', 'extreme_greed', 'neutral'])
        
        if phase == 'extreme_fear':
            value = random.randint(5, 25)
        elif phase == 'fear':
            value = random.randint(25, 45)
        elif phase == 'neutral':
            value = random.randint(45, 55)
        elif phase == 'greed':
            value = random.randint(55, 75)
        else:  # extreme_greed
            value = random.randint(75, 95)
        
        classifications = {
            (0, 25): "Extreme Fear",
            (25, 45): "Fear",
            (45, 55): "Neutral",
            (55, 75): "Greed",
            (75, 100): "Extreme Greed"
        }
        
        classification = "Neutral"
        for (low, high), name in classifications.items():
            if low <= value < high:
                classification = name
                break
        
        change = random.randint(-15, 15)
        
        return value, classification, change
    
    async def fetch_sentiment(self) -> SentimentMetrics:
        """Generate mock sentiment metrics."""
        import random
        
        value, classification, change = await self.fetch_fng()
        
        # Generate social metrics correlated with F&G
        if classification == "Extreme Greed":
            social_volume = random.randint(50000, 100000)
            sentiment = random.uniform(0.6, 0.9)
            bullish_ratio = random.uniform(0.7, 0.9)
        elif classification == "Extreme Fear":
            social_volume = random.randint(10000, 30000)
            sentiment = random.uniform(-0.9, -0.5)
            bullish_ratio = random.uniform(0.2, 0.4)
        elif classification == "Greed":
            social_volume = random.randint(30000, 60000)
            sentiment = random.uniform(0.3, 0.6)
            bullish_ratio = random.uniform(0.55, 0.7)
        elif classification == "Fear":
            social_volume = random.randint(15000, 40000)
            sentiment = random.uniform(-0.6, -0.2)
            bullish_ratio = random.uniform(0.35, 0.5)
        else:
            social_volume = random.randint(20000, 50000)
            sentiment = random.uniform(-0.2, 0.2)
            bullish_ratio = random.uniform(0.45, 0.55)
        
        return SentimentMetrics(
            fng_value=value,
            fng_classification=classification,
            fng_change_24h=change,
            social_volume=social_volume,
            social_engagement=random.uniform(1000000, 5000000),
            sentiment_score=sentiment,
            sentiment_trend="rising" if change > 5 else "falling" if change < -5 else "stable",
            bullish_ratio=bullish_ratio,
            timestamp=datetime.now()
        )


class SentimentClassifier:
    """Classifies sentiment and generates contrarian signals."""
    
    def __init__(self):
        # Historical accuracy stats
        self.fear_buy_accuracy = 0.76     # 76% historically
        self.greed_pullback_accuracy = 0.68  # 68% pullback chance
    
    def classify(self, metrics: SentimentMetrics) -> SentimentSignal:
        """Classify sentiment and generate contrarian signal."""
        
        # Classify F&G level
        if metrics.fng_value < 25:
            level = SentimentLevel.EXTREME_FEAR
            is_extreme = True
            extreme_type = "fear"
            contrarian_signal = "BUY"
            confidence = min(0.95, (25 - metrics.fng_value) / 25 + 0.5)
        elif metrics.fng_value < 45:
            level = SentimentLevel.FEAR
            is_extreme = False
            extreme_type = ""
            contrarian_signal = "HOLD"
            confidence = 0.6
        elif metrics.fng_value < 55:
            level = SentimentLevel.NEUTRAL
            is_extreme = False
            extreme_type = ""
            contrarian_signal = "HOLD"
            confidence = 0.5
        elif metrics.fng_value < 75:
            level = SentimentLevel.GREED
            is_extreme = False
            extreme_type = ""
            contrarian_signal = "HOLD"
            confidence = 0.6
        else:
            level = SentimentLevel.EXTREME_GREED
            is_extreme = True
            extreme_type = "greed"
            contrarian_signal = "SELL"
            confidence = min(0.95, (metrics.fng_value - 75) / 25 + 0.5)
        
        # Calculate contrarian strength
        if is_extreme:
            if extreme_type == "fear":
                contrarian_strength = (25 - metrics.fng_value) / 25
                historical_accuracy = self.fear_buy_accuracy
            else:
                contrarian_strength = (metrics.fng_value - 75) / 25
                historical_accuracy = self.greed_pullback_accuracy
        else:
            contrarian_strength = abs(metrics.fng_value - 50) / 50
            historical_accuracy = 0.5
        
        # Generate interpretation
        interpretation = self._generate_interpretation(level, metrics)
        
        return SentimentSignal(
            level=level,
            value=metrics.fng_value,
            confidence=confidence,
            is_extreme=is_extreme,
            extreme_type=extreme_type,
            buy_signal=extreme_type == "fear",
            historical_accuracy=historical_accuracy,
            contrarian_signal=contrarian_signal,
            contrarian_strength=contrarian_strength,
            interpretation=interpretation
        )
    
    def cross_check(self, signal: SentimentSignal, 
                   onchain_regime: str, macro_regime: str) -> SentimentSignal:
        """Check if sentiment confirms or contradicts fundamentals."""
        
        signal.onchain_regime = onchain_regime
        signal.macro_regime = macro_regime
        
        # Define aligned combinations
        # When sentiment agrees with fundamentals
        aligned = [
            # Extreme fear + accumulation + tailwind = CONFIRM
            ("fear", "accumulation", "crypto_tailwind"),
            # Extreme greed + distribution + headwind = CONFIRM
            ("greed", "distribution", "crypto_headwind"),
            # Neutral sentiment + transition regime = CONFIRM
            ("neutral", "transition", "neutral"),
        ]
        
        signal_lower = signal.extreme_type.lower() if signal.extreme_type else "neutral"
        
        for sent_type, onchain, macro in aligned:
            if signal_lower == sent_type and onchain in onchain_regime.lower() and macro in macro_regime.lower():
                signal.confirmation_signal = "CONFIRMED"
                signal.alignment_with_fundamentals = True
                signal.interpretation += f" Sentiment {signal.extreme_type or 'neutral'} confirms {onchain_regime} + {macro_regime}."
                return signal
        
        # Check for contradictions
        contradictions = [
            ("fear", "distribution", "crypto_tailwind"),  # On-chain says distribution but F&G says fear
            ("greed", "accumulation", "crypto_headwind"),   # Opposite
        ]
        
        for sent_type, onchain, macro in contradictions:
            if signal_lower == sent_type and onchain in onchain_regime.lower() and macro in macro_regime.lower():
                signal.confirmation_signal = "CONTRADICTED"
                signal.alignment_with_fundamentals = False
                signal.interpretation += f" ⚠️ WARNING: Sentiment contradicts {onchain_regime} + {macro_regime}!"
                return signal
        
        # Neutral
        signal.confirmation_signal = "NEUTRAL"
        signal.alignment_with_fundamentals = False
        signal.interpretation += f" Sentiment does not clearly confirm/contradict."
        
        return signal
    
    def _generate_interpretation(self, level: SentimentLevel, m: SentimentMetrics) -> str:
        """Generate interpretation."""
        
        if level == SentimentLevel.EXTREME_FEAR:
            return (
                f"😱 **Extreme Fear Detected** (F&G: {m.fng_value}). "
                f"Historically a BUY signal with {self.fear_buy_accuracy:.0%} accuracy. "
                f"Social volume low ({m.social_volume:,}) indicates capitulation. "
                f"Contrarian opportunity may be imminent."
            )
        elif level == SentimentLevel.FEAR:
            return (
                f"😰 **Fear in Market** (F&G: {m.fng_value}). "
                f"Room for continued selling but potential bottoming forming. "
                f"Watch for reversal signals."
            )
        elif level == SentimentLevel.NEUTRAL:
            return (
                f"😐 **Sentiment Neutral** (F&G: {m.fng_value}). "
                f"No clear directional bias. "
                f"Market in equilibrium - await catalyst."
            )
        elif level == SentimentLevel.GREED:
            return (
                f"🤑 **Greed Building** (F&G: {m.fng_value}). "
                f"Caution warranted - trend may be maturing. "
                f"Watch for reversal signs."
            )
        else:  # EXTREME_GREED
            return (
                f"🤪 **Extreme Greed** (F&G: {m.fng_value}). "
                f"Historically precedes pullbacks {self.greed_pullback_accuracy:.0%} of the time. "
                f"High social volume ({m.social_volume:,}) indicates euphoric sentiment. "
                f"Risk management critical."
            )


class SentimentDetector:
    """Main class for sentiment detection."""
    
    def __init__(self, fng_provider=None, social_provider=None):
        self.fng_provider = fng_provider or MockSentimentProvider()
        self.social_provider = social_provider or MockSentimentProvider()
        self.classifier = SentimentClassifier()
        self._last_signal: Optional[SentimentSignal] = None
        self._last_metrics: Optional[SentimentMetrics] = None
    
    async def get_sentiment_signal(self, use_cache: bool = False) -> SentimentSignal:
        """Get current sentiment signal."""
        if use_cache and self._last_signal:
            age = (datetime.now() - self._last_metrics.timestamp).total_seconds()
            if age < 300:
                return self._last_signal
        
        # Fetch metrics
        metrics = await self.fng_provider.fetch_sentiment()
        
        # Classify
        signal = self.classifier.classify(metrics)
        
        self._last_signal = signal
        self._last_metrics = metrics
        
        return signal
    
    async def get_metrics(self) -> SentimentMetrics:
        """Get raw sentiment metrics."""
        if not self._last_metrics:
            self._last_metrics = await self.fng_provider.fetch_sentiment()
        return self._last_metrics
    
    def analyze_alignment(self, onchain_regime: str, macro_regime: str) -> SentimentSignal:
        """Get sentiment and cross-check with regimes."""
        if not self._last_signal:
            return SentimentSignal(
                level=SentimentLevel.UNKNOWN,
                value=50,
                confidence=0,
                is_extreme=False,
                extreme_type="",
                buy_signal=False,
                historical_accuracy=0,
                contrarian_signal="HOLD",
                contrarian_strength=0,
                interpretation="No data available"
            )
        
        return self.classifier.cross_check(self._last_signal, onchain_regime, macro_regime)
    
    def get_trade_recommendation(self, signal: SentimentSignal) -> Dict[str, Any]:
        """Get trading recommendation based on sentiment."""
        
        if signal.extreme_type == "fear":
            return {
                "action": "BUY",
                "position": "add_to_long",
                "target": "aggressive",
                "stop_loss": "normal",
                "notes": f"Extreme fear - {signal.historical_accuracy:.0%} historical bounce rate"
            }
        elif signal.extreme_type == "greed":
            return {
                "action": "SELL",
                "position": "reduce_exposure",
                "target": "take_profit",
                "stop_loss": "tight",
                "notes": f"Extreme greed - {signal.historical_accuracy:.0%}% pullback probability"
            }
        elif signal.confirmation_signal == "CONFIRMED":
            return {
                "action": "HOLD" if signal.onchain_regime == "accumulation" else "REDUCE",
                "position": "maintain",
                "target": "normal",
                "stop_loss": "normal",
                "notes": "Sentiment confirms fundamental regime"
            }
        elif signal.confirmation_signal == "CONTRADICTED":
            return {
                "action": "CAUTION",
                "position": "reduce",
                "target": "tight",
                "stop_loss": "very_tight",
                "notes": "Sentiment contradicts fundamentals - await clarity"
            }
        else:
            return {
                "action": "HOLD",
                "position": "maintain",
                "target": "normal",
                "stop_loss": "normal",
                "notes": "Sentiment neutral - no clear signal"
            }
