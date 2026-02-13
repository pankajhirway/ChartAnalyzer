"""Fundamental data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
