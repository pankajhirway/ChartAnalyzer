"""Fundamental data models."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


@dataclass
class FundamentalScore:
    """Result from fundamental scoring analysis."""
    score: float
    grade: str
    bullish_factors: list[str]
    bearish_factors: list[str]
    warnings: list[str]
    detail_scores: dict[str, float]

    class Config:
        json_schema_extra = {
            "example": {
                "score": 72.5,
                "grade": "B+",
                "bullish_factors": ["Attractive P/E ratio (18.5)", "Strong ROE (18.2%)"],
                "bearish_factors": ["Moderate-high debt (1.2)"],
                "warnings": [],
                "detail_scores": {
                    "pe_score": 20.0,
                    "growth_score": 22.5,
                    "roe_score": 18.0,
                    "debt_score": 12.0
                }
            }
        }


class FundamentalData(BaseModel):
    """Fundamental metrics model for stock analysis."""
    symbol: str = Field(..., description="NSE/BSE symbol (e.g., RELIANCE)")
    pe_ratio: Optional[float] = Field(None, description="Price-to-Earnings ratio")
    pb_ratio: Optional[float] = Field(None, description="Price-to-Book ratio")
    roe: Optional[float] = Field(None, description="Return on Equity (%)")
    roce: Optional[float] = Field(None, description="Return on Capital Employed (%)")
    debt_to_equity: Optional[float] = Field(None, description="Debt-to-Equity ratio")
    eps_growth: Optional[float] = Field(None, description="Earnings Per Share growth (%)")
    revenue_growth: Optional[float] = Field(None, description="Revenue growth (%)")
    updated_at: Optional[datetime] = Field(None, description="Last updated timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "pe_ratio": 24.5,
                "pb_ratio": 1.8,
                "roe": 12.5,
                "roce": 10.2,
                "debt_to_equity": 0.45,
                "eps_growth": 8.5,
                "revenue_growth": 15.2,
                "updated_at": "2024-01-15T09:15:00"
            }
        }


class FundamentalDataCache(Base):
    """Database model for caching fundamental data with quarterly update tracking.

    This table stores cached fundamental metrics to reduce external API calls.
    Data is updated quarterly when financial results are announced.
    """

    __tablename__ = "fundamental_data_cache"

    # Primary key - stock symbol
    symbol: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Fundamental metrics
    pe_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pb_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roce: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    debt_to_equity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eps_growth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_growth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<FundamentalDataCache(symbol={self.symbol}, pe_ratio={self.pe_ratio})>"

