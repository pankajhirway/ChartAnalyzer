"""Scanner preset models and definitions."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PresetType(str, Enum):
    """Scanner preset type enumeration."""
    MINERVINI_BREAKOUTS = "MINERVINI_BREAKOUTS"
    STAGE_2_STOCKS = "STAGE_2_STOCKS"
    VCP_SETUPS = "VCP_SETUPS"
    HIGH_COMPOSITE_SCORE = "HIGH_COMPOSITE_SCORE"
    VOLUME_BREAKOUTS = "VOLUME_BREAKOUTS"
    PULLBACK_ENTRIES = "PULLBACK_ENTRIES"
    HIGH_CONVLECTION = "HIGH_CONVLECTION"


class UniverseType(str, Enum):
    """Stock universe enumeration."""
    NIFTY_50 = "NIFTY_50"
    NIFTY_200 = "NIFTY_200"
    NIFTY_500 = "NIFTY_500"
    CUSTOM = "CUSTOM"


class PresetFilter(BaseModel):
    """Filter criteria for scanner preset."""
    min_composite_score: float = Field(default=50.0, description="Minimum composite score")
    max_composite_score: float = Field(default=100.0, description="Maximum composite score")
    signal: Optional[str] = Field(None, description="Signal filter: BUY, SELL, HOLD, AVOID")
    min_conviction: Optional[str] = Field(None, description="Minimum conviction: HIGH, MEDIUM, LOW")
    min_volume_ratio: Optional[float] = Field(None, description="Minimum volume ratio")
    trend: Optional[str] = Field(None, description="Trend filter: BULLISH, BEARISH, NEUTRAL")
    weinstein_stage: Optional[int] = Field(None, description="Weinstein stage filter: 1, 2, 3, 4")

    class Config:
        json_schema_extra = {
            "example": {
                "min_composite_score": 65.0,
                "max_composite_score": 100.0,
                "signal": "BUY",
                "min_conviction": "MEDIUM",
                "min_volume_ratio": 1.5,
                "trend": "BULLISH",
                "weinstein_stage": 2
            }
        }


class ScannerPreset(BaseModel):
    """Scanner preset model."""
    id: str = Field(..., description="Unique preset identifier")
    name: str = Field(..., description="Preset display name")
    description: str = Field(..., description="Preset description")
    strategy_rationale: str = Field(..., description="Why this strategy works")
    filter: PresetFilter = Field(..., description="Filter criteria")
    recommended_universe: UniverseType = Field(..., description="Recommended universe for this preset")
    holding_period: str = Field(default="SWING", description="Recommended holding period")
    difficulty: str = Field(default="beginner", description="Difficulty level: beginner, intermediate, advanced")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "minervini_breakouts",
                "name": "Minervini Breakouts",
                "description": "Stocks showing VCP or base breakout patterns",
                "strategy_rationale": "Based on Mark Minervini's SEPA strategy, focuses on stocks breaking out of proper bases with volume confirmation.",
                "filter": {
                    "min_composite_score": 65.0,
                    "signal": "BUY"
                },
                "recommended_universe": "NIFTY_200",
                "holding_period": "SWING",
                "difficulty": "intermediate"
            }
        }


def get_enhanced_presets() -> dict[str, ScannerPreset]:
    """Get enhanced scanner preset definitions.

    Returns:
        Dictionary mapping preset IDs to ScannerPreset objects
    """
    return {
        "minervini_breakouts": ScannerPreset(
            id="minervini_breakouts",
            name="Minervini Breakouts",
            description="Stocks showing VCP (Volatility Contraction Pattern) or base breakout patterns with volume confirmation",
            strategy_rationale=(
                "Based on Mark Minervini's SEPA (Specific Entry Point Analysis) strategy. "
                "VCP patterns show decreasing volatility as the base forms, indicating supply "
                "absorption. Breakouts from such patterns, especially with volume confirmation, "
                "have a high probability of success. The strategy identifies stocks in Stage 2 "
                "uptrends breaking out of constructive consolidation periods."
            ),
            filter=PresetFilter(
                min_composite_score=65.0,
                signal="BUY",
                min_volume_ratio=1.2,
            ),
            recommended_universe=UniverseType.NIFTY_200,
            holding_period="SWING",
            difficulty="intermediate",
        ),
        "stage_2_stocks": ScannerPreset(
            id="stage_2_stocks",
            name="Stage 2 Stocks",
            description="Stocks in Weinstein Stage 2 (advancing phase) with strong uptrend characteristics",
            strategy_rationale=(
                "Based on Stan Weinstein's stage theory. Stage 2 is the 'advancing' phase where "
                "stocks break above 30-week moving average and establish higher highs and higher "
                "lows. This is the optimal time to be long as institutional accumulation typically "
                "occurs in this phase. Stocks in Stage 2 with bullish trends have historically "
                "outperformed the market."
            ),
            filter=PresetFilter(
                min_composite_score=55.0,
                trend="BULLISH",
                weinstein_stage=2,
            ),
            recommended_universe=UniverseType.NIFTY_200,
            holding_period="POSITIONAL",
            difficulty="beginner",
        ),
        "vcp_setups": ScannerPreset(
            id="vcp_setups",
            name="VCP Setups",
            description="Volatility Contraction Pattern setups - tightening price action with decreasing volatility",
            strategy_rationale=(
                "VCP is Mark Minervini's signature pattern. It shows successive contractions "
                "in price range and volume, indicating that sellers are exhausted and supply is "
                "being absorbed by stronger hands. The pattern typically has 3-5 contractions, "
                "with each contraction smaller than the previous. As the pattern tightens, the "
                "stock becomes coiled for a potential explosive move when breakout occurs."
            ),
            filter=PresetFilter(
                min_composite_score=60.0,
                signal="BUY",
            ),
            recommended_universe=UniverseType.NIFTY_200,
            holding_period="SWING",
            difficulty="advanced",
        ),
        "high_composite_score": ScannerPreset(
            id="high_composite_score",
            name="High Composite Score",
            description="Stocks with highest composite technical scores across all analysis dimensions",
            strategy_rationale=(
                "The composite score combines multiple technical indicators, trend strength, "
                "pattern detection, and strategy alignment into a single metric. High composite "
                "scores indicate stocks that are performing well across multiple dimensions: "
                "strong trend, positive momentum, supportive technical indicators, and presence "
                "of bullish patterns. This multi-factor approach reduces false positives and "
                "identifies the strongest opportunities."
            ),
            filter=PresetFilter(
                min_composite_score=75.0,
                signal="BUY",
                min_conviction="MEDIUM",
            ),
            recommended_universe=UniverseType.NIFTY_200,
            holding_period="SWING",
            difficulty="beginner",
        ),
        "volume_breakouts": ScannerPreset(
            id="volume_breakouts",
            name="Volume Breakouts",
            description="Stocks breaking above resistance with significant volume increase (52-week high focus)",
            strategy_rationale=(
                "Volume confirms the validity of price movements. A breakout above resistance "
                "with above-average volume indicates institutional participation and genuine "
                "accumulation. Stocks hitting 52-week highs with volume often continue higher as "
                "new buyers enter and short sellers get squeezed. This preset specifically targets "
                "stocks breaking to new highs with 1.5x or higher average volume."
            ),
            filter=PresetFilter(
                min_composite_score=60.0,
                signal="BUY",
                min_volume_ratio=1.5,
            ),
            recommended_universe=UniverseType.NIFTY_200,
            holding_period="SWING",
            difficulty="beginner",
        ),
        "pullback_entries": ScannerPreset(
            id="pullback_entries",
            name="Pullback Entries",
            description="Stocks in uptrend pulling back to key moving averages or support zones",
            strategy_rationale=(
                "In established uptrends, pullbacks to support areas (like 21-day EMA or 50-day SMA) "
                "offer favorable risk-reward entry points. Instead of chasing breakouts, this preset "
                "identifies stocks in Stage 2 that are experiencing temporary weakness within the "
                "context of a larger uptrend. These pullbacks provide opportunities to enter strong "
                "stocks at better prices with closer stops."
            ),
            filter=PresetFilter(
                min_composite_score=50.0,
                max_composite_score=75.0,
                trend="BULLISH",
                weinstein_stage=2,
            ),
            recommended_universe=UniverseType.NIFTY_200,
            holding_period="SWING",
            difficulty="intermediate",
        ),
        "high_conviction": ScannerPreset(
            id="high_conviction",
            name="High Conviction",
            description="High conviction buy signals where multiple indicators and strategies align",
            strategy_rationale=(
                "High conviction signals occur when multiple independent analysis methods align: "
                "Minervini criteria are met, Weinstein Stage 2 is confirmed, multiple bullish patterns "
                "are detected, and technical indicators are supportive. This convergence reduces "
                "uncertainty and increases probability of success. These setups are suitable for "
                "larger position sizes due to higher confidence levels."
            ),
            filter=PresetFilter(
                min_composite_score=70.0,
                signal="BUY",
                min_conviction="HIGH",
            ),
            recommended_universe=UniverseType.NIFTY_50,
            holding_period="POSITIONAL",
            difficulty="beginner",
        ),
    }
