"""Analysis result models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TrendType(str, Enum):
    """Trend direction enumeration."""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class PatternType(str, Enum):
    """Chart pattern types enumeration."""
    CUP_HANDLE = "CUP_HANDLE"
    VCP = "VCP"
    DOUBLE_TOP = "DOUBLE_TOP"
    DOUBLE_BOTTOM = "DOUBLE_BOTTOM"
    HEAD_SHOULDERS = "HEAD_SHOULDERS"
    HEAD_SHOULDERS_INVERSE = "HEAD_SHOULDERS_INVERSE"
    ASCENDING_TRIANGLE = "ASCENDING_TRIANGLE"
    DESCENDING_TRIANGLE = "DESCENDING_TRIANGLE"
    FLAG = "FLAG"
    PENNANT = "PENNANT"
    WEDGE_RISING = "WEDGE_RISING"
    WEDGE_FALLING = "WEDGE_FALLING"
    BASE_BREAKOUT = "BASE_BREAKOUT"
    HIGH_TIGHT_FLAG = "HIGH_TIGHT_FLAG"
    PULLBACK_MA = "PULLBACK_MA"


class SignalType(str, Enum):
    """Signal type enumeration."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    AVOID = "AVOID"


class ConvictionLevel(str, Enum):
    """Conviction level enumeration."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class HoldingPeriod(str, Enum):
    """Holding period enumeration."""
    INTRADAY = "INTRADAY"
    SWING = "SWING"
    POSITIONAL = "POSITIONAL"


class WeinsteinStage(int, Enum):
    """Weinstein stage enumeration."""
    STAGE_1 = 1  # Basing
    STAGE_2 = 2  # Advancing
    STAGE_3 = 3  # Topping
    STAGE_4 = 4  # Declining


class Level(BaseModel):
    """Support/Resistance level model."""
    price: float = Field(..., description="Price level")
    strength: int = Field(..., ge=1, le=5, description="Strength (1-5)")
    touches: int = Field(default=1, description="Number of touches")
    level_type: str = Field(..., description="Type: support/resistance/pivot")
    description: Optional[str] = Field(None, description="Human-readable description")

    class Config:
        json_schema_extra = {
            "example": {
                "price": 2500.00,
                "strength": 4,
                "touches": 3,
                "level_type": "resistance",
                "description": "Previous swing high resistance"
            }
        }


class PatternMatch(BaseModel):
    """Detected pattern match model."""
    pattern_type: PatternType
    pattern_name: str = Field(..., description="Human-readable pattern name")
    bullish: bool = Field(..., description="Whether pattern is bullish")
    completion_pct: float = Field(..., ge=0, le=100, description="Pattern completion percentage")
    breakout_level: Optional[float] = Field(None, description="Breakout price level")
    target_price: Optional[float] = Field(None, description="Pattern target price")
    stop_loss: Optional[float] = Field(None, description="Pattern stop loss level")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    description: str = Field(..., description="Pattern description")

    class Config:
        json_schema_extra = {
            "example": {
                "pattern_type": "VCP",
                "pattern_name": "Volatility Contraction Pattern",
                "bullish": True,
                "completion_pct": 85.0,
                "breakout_level": 2500.00,
                "target_price": 2750.00,
                "stop_loss": 2400.00,
                "confidence": 0.82,
                "description": "VCP with 3 contractions, tightening price action"
            }
        }


class Indicators(BaseModel):
    """Technical indicators model."""
    # Moving Averages
    sma_10: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_150: Optional[float] = None
    sma_200: Optional[float] = None
    ema_8: Optional[float] = None
    ema_21: Optional[float] = None

    # MACD
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None

    # RSI
    rsi_14: Optional[float] = None

    # Stochastic
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None

    # Bollinger Bands
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None

    # ATR
    atr_14: Optional[float] = None

    # ADX
    adx_14: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None

    # Volume
    volume_sma_20: Optional[float] = None
    volume_sma_50: Optional[float] = None
    obv: Optional[float] = None
    obv_sma: Optional[float] = None

    # Relative Strength
    relative_strength: Optional[float] = Field(None, description="RS vs Nifty 50")

    class Config:
        json_schema_extra = {
            "example": {
                "sma_10": 2470.0,
                "sma_20": 2450.0,
                "sma_50": 2400.0,
                "sma_150": 2350.0,
                "sma_200": 2300.0,
                "ema_8": 2475.0,
                "ema_21": 2460.0,
                "macd": 15.5,
                "macd_signal": 12.3,
                "macd_histogram": 3.2,
                "rsi_14": 62.5,
                "stoch_k": 75.0,
                "stoch_d": 70.0,
                "bb_upper": 2520.0,
                "bb_middle": 2450.0,
                "bb_lower": 2380.0,
                "bb_width": 5.7,
                "atr_14": 45.0,
                "adx_14": 28.5,
                "plus_di": 25.0,
                "minus_di": 18.0,
                "volume_sma_20": 7500000,
                "volume_sma_50": 7000000,
                "obv": 1500000000,
                "obv_sma": 1450000000,
                "relative_strength": 1.15
            }
        }


class StrategyScores(BaseModel):
    """Individual strategy scores."""
    minervini_score: float = Field(..., ge=0, le=100)
    weinstein_score: float = Field(..., ge=0, le=100)
    lynch_score: Optional[float] = Field(None, ge=0, le=100)
    technical_score: float = Field(..., ge=0, le=100)
    fundamental_score: Optional[float] = Field(None, ge=0, le=100)
    composite_score: float = Field(..., ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "minervini_score": 78.5,
                "weinstein_score": 82.0,
                "lynch_score": 65.0,
                "technical_score": 75.0,
                "fundamental_score": 70.0,
                "composite_score": 76.5
            }
        }


class AnalysisResult(BaseModel):
    """Complete analysis result model."""
    symbol: str
    company_name: Optional[str] = None
    timestamp: datetime
    timeframe: str
    current_price: float

    # Trend Analysis
    primary_trend: TrendType
    trend_strength: float = Field(..., ge=0, le=100)
    trend_notes: Optional[str] = None

    # Stage Analysis
    weinstein_stage: WeinsteinStage
    stage_description: Optional[str] = None

    # Scores
    scores: StrategyScores

    # Patterns
    detected_patterns: list[PatternMatch]

    # Levels
    support_levels: list[Level]
    resistance_levels: list[Level]

    # Overall Signal
    signal: SignalType
    conviction: ConvictionLevel

    # Indicators
    indicators: Indicators

    # Analysis Notes
    bullish_factors: list[str] = Field(default_factory=list)
    bearish_factors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "company_name": "Reliance Industries Ltd",
                "timestamp": "2024-01-15T15:30:00",
                "timeframe": "1d",
                "current_price": 2475.25,
                "primary_trend": "BULLISH",
                "trend_strength": 72.5,
                "trend_notes": "Strong uptrend with higher highs",
                "weinstein_stage": 2,
                "stage_description": "Advancing stage - Buy zone",
                "scores": {
                    "minervini_score": 78.5,
                    "weinstein_score": 82.0,
                    "lynch_score": 65.0,
                    "technical_score": 75.0,
                    "composite_score": 76.5
                },
                "detected_patterns": [],
                "support_levels": [],
                "resistance_levels": [],
                "signal": "BUY",
                "conviction": "MEDIUM",
                "indicators": {},
                "bullish_factors": ["Price above all key MAs", "Volume on up days"],
                "bearish_factors": [],
                "warnings": ["Approaching 52-week high"]
            }
        }
