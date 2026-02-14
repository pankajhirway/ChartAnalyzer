"""Stock data models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Exchange(str, Enum):
    """Stock exchange enumeration."""
    NSE = "NSE"
    BSE = "BSE"


class Stock(BaseModel):
    """Stock information model."""
    symbol: str = Field(..., description="NSE/BSE symbol (e.g., RELIANCE)")
    company_name: str = Field(..., description="Full company name")
    exchange: Exchange = Field(default=Exchange.NSE, description="Stock exchange")
    sector: Optional[str] = Field(None, description="Sector classification")
    industry: Optional[str] = Field(None, description="Industry classification")
    market_cap: Optional[float] = Field(None, description="Market capitalization in crores")
    isin: Optional[str] = Field(None, description="ISIN code")
    face_value: Optional[float] = Field(None, description="Face value of shares")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "company_name": "Reliance Industries Ltd",
                "exchange": "NSE",
                "sector": "Energy",
                "industry": "Refineries",
                "market_cap": 1800000.0,
                "isin": "INE002A01018",
                "face_value": 10.0
            }
        }


class PriceData(BaseModel):
    """OHLCV price data model."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: Optional[float] = Field(None, description="Adjusted close price")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "timestamp": "2024-01-15T09:15:00",
                "open": 2450.00,
                "high": 2480.50,
                "low": 2445.00,
                "close": 2475.25,
                "volume": 8500000,
                "adj_close": 2475.25
            }
        }


class PriceDataResponse(BaseModel):
    """Response model for historical price data."""
    symbol: str
    timeframe: str
    data: list[PriceData]

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "timeframe": "1d",
                "data": []
            }
        }


class StockQuote(BaseModel):
    """Real-time stock quote model."""
    symbol: str
    company_name: Optional[str] = None
    last_price: float
    change: float
    change_percent: float
    day_high: float
    day_low: float
    day_open: float
    prev_close: float
    volume: int
    avg_volume: Optional[int] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "company_name": "Reliance Industries Ltd",
                "last_price": 2475.25,
                "change": 25.25,
                "change_percent": 1.03,
                "day_high": 2480.50,
                "day_low": 2445.00,
                "day_open": 2450.00,
                "prev_close": 2450.00,
                "volume": 8500000,
                "avg_volume": 7500000,
                "fifty_two_week_high": 2800.00,
                "fifty_two_week_low": 2100.00,
                "timestamp": "2024-01-15T15:30:00"
            }
        }


class StockSearchResult(BaseModel):
    """Stock search result model."""
    symbol: str
    company_name: str
    exchange: Exchange
    sector: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "company_name": "Reliance Industries Ltd",
                "exchange": "NSE",
                "sector": "Energy"
            }
        }


class BatchHistoryRequest(BaseModel):
    """Request model for batch historical data."""
    timeframes: list[str] = Field(..., description="List of timeframes (e.g., ['1d', '1w', '1h'])")
    days: int = Field(365, ge=30, le=730, description="Number of days of history")

    class Config:
        json_schema_extra = {
            "example": {
                "timeframes": ["1d", "1w", "1h"],
                "days": 180
            }
        }


class BatchHistoryResponse(BaseModel):
    """Response model for batch historical data."""
    symbol: str
    days: int
    data: dict[str, PriceDataResponse] = Field(..., description="Map of timeframe to price data")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "days": 180,
                "data": {
                    "1d": {
                        "symbol": "RELIANCE",
                        "timeframe": "1d",
                        "data": []
                    }
                }
            }
        }
