"""Trade suggestion models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.models.analysis import (
    SignalType,
    ConvictionLevel,
    HoldingPeriod,
)


class StopLossType(str, Enum):
    """Stop loss type enumeration."""
    PERCENTAGE = "PERCENTAGE"
    ATR = "ATR"
    SUPPORT = "SUPPORT"
    SWING_LOW = "SWING_LOW"


class EntryZone(BaseModel):
    """Entry zone for trade execution."""
    low: float = Field(..., description="Lower bound of entry zone")
    high: float = Field(..., description="Upper bound of entry zone")

    class Config:
        json_schema_extra = {
            "example": {
                "low": 2480.00,
                "high": 2500.00
            }
        }


class Target(BaseModel):
    """Trade target model."""
    price: float = Field(..., description="Target price")
    risk_reward: float = Field(..., description="Risk/reward ratio at this target")
    description: Optional[str] = Field(None, description="Target description")

    class Config:
        json_schema_extra = {
            "example": {
                "price": 2650.00,
                "risk_reward": 2.0,
                "description": "Conservative target - previous resistance"
            }
        }


class TradeSuggestion(BaseModel):
    """Complete trade suggestion model."""
    symbol: str
    timestamp: datetime

    # Action
    action: SignalType
    conviction: ConvictionLevel

    # Entry Details
    entry_price: float = Field(..., description="Suggested entry price")
    entry_zone: EntryZone = Field(..., description="Entry zone for limit orders")
    entry_trigger: str = Field(..., description="What triggers the entry")

    # Risk Management
    stop_loss: float = Field(..., description="Stop loss price")
    stop_loss_type: StopLossType = Field(..., description="Stop loss calculation method")
    stop_loss_pct: float = Field(..., description="Stop loss percentage")
    risk_per_share: float = Field(..., description="Risk amount per share")

    # Targets
    target_1: Target = Field(..., description="Conservative target")
    target_2: Target = Field(..., description="Moderate target")
    target_3: Target = Field(..., description="Aggressive target")

    # Position Sizing
    suggested_position_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Suggested position as % of portfolio"
    )
    max_position_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Maximum position as % of portfolio"
    )

    # Risk/Reward
    risk_reward_ratio: float = Field(..., description="Primary risk/reward ratio")

    # Timeframe
    holding_period: HoldingPeriod
    expected_days: Optional[int] = Field(None, description="Expected holding days")

    # Metadata
    strategy_source: str = Field(..., description="Which strategy triggered this")
    reasoning: list[str] = Field(..., description="Bullet points explaining the trade")
    warnings: list[str] = Field(default_factory=list, description="Risk factors to consider")

    # Market Context
    market_trend: Optional[str] = Field(None, description="Current market trend context")
    sector_trend: Optional[str] = Field(None, description="Sector trend context")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "timestamp": "2024-01-15T15:30:00",
                "action": "BUY",
                "conviction": "MEDIUM",
                "entry_price": 2490.00,
                "entry_zone": {"low": 2480.00, "high": 2500.00},
                "entry_trigger": "Breakout above 2500 resistance with volume",
                "stop_loss": 2400.00,
                "stop_loss_type": "SUPPORT",
                "stop_loss_pct": 3.6,
                "risk_per_share": 90.00,
                "target_1": {
                    "price": 2650.00,
                    "risk_reward": 2.0,
                    "description": "Conservative target"
                },
                "target_2": {
                    "price": 2750.00,
                    "risk_reward": 3.0,
                    "description": "Moderate target"
                },
                "target_3": {
                    "price": 2900.00,
                    "risk_reward": 4.5,
                    "description": "Aggressive target"
                },
                "suggested_position_pct": 5.0,
                "max_position_pct": 8.0,
                "risk_reward_ratio": 2.5,
                "holding_period": "SWING",
                "expected_days": 15,
                "strategy_source": "Minervini SEPA + Weinstein Stage 2",
                "reasoning": [
                    "VCP breakout forming",
                    "Price above all key moving averages",
                    "Volume expanding on up days",
                    "Market in uptrend"
                ],
                "warnings": ["Approaching 52-week high", "Earnings in 2 weeks"],
                "market_trend": "BULLISH",
                "sector_trend": "BULLISH"
            }
        }


class TradePlan(BaseModel):
    """Complete trade plan with multiple scenarios."""
    symbol: str
    company_name: Optional[str] = None
    timestamp: datetime
    current_price: float

    # Primary trade
    primary_trade: TradeSuggestion

    # Alternative scenarios
    alternative_entries: list[TradeSuggestion] = Field(default_factory=list)

    # Position management
    scale_in_levels: list[float] = Field(default_factory=list, description="Prices to add to position")
    scale_out_levels: list[float] = Field(default_factory=list, description="Prices to take partial profits")

    # Trail stop suggestions
    trail_stop_trigger: Optional[float] = Field(None, description="Price to start trailing stop")
    trail_stop_method: Optional[str] = Field(None, description="Trailing stop method")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "company_name": "Reliance Industries Ltd",
                "timestamp": "2024-01-15T15:30:00",
                "current_price": 2475.25,
                "primary_trade": {},
                "alternative_entries": [],
                "scale_in_levels": [2520.00, 2580.00],
                "scale_out_levels": [2650.00, 2750.00],
                "trail_stop_trigger": 2600.00,
                "trail_stop_method": "Trail below 20 EMA"
            }
        }
