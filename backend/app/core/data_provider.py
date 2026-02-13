"""Unified data provider interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.models.stock import Stock, PriceData, StockQuote, StockSearchResult
from app.models.fundamental import FundamentalData


class DataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    async def get_stock_info(self, symbol: str) -> Optional[Stock]:
        """Get stock information by symbol.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")

        Returns:
            Stock object or None if not found
        """
        pass

    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = "1d",
    ) -> list[PriceData]:
        """Get historical price data.

        Args:
            symbol: Stock symbol
            start_date: Start date for data
            end_date: End date for data
            timeframe: Data timeframe (1d, 1h, 1w, etc.)

        Returns:
            List of PriceData objects
        """
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get real-time quote for a stock.

        Args:
            symbol: Stock symbol

        Returns:
            StockQuote object or None if not found
        """
        pass

    @abstractmethod
    async def search_stocks(self, query: str, limit: int = 10) -> list[StockSearchResult]:
        """Search for stocks by name or symbol.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching stocks
        """
        pass

    @abstractmethod
    async def get_multiple_quotes(self, symbols: list[str]) -> dict[str, StockQuote]:
        """Get quotes for multiple stocks.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to quotes
        """
        pass

    def format_indian_symbol(self, symbol: str) -> str:
        """Format symbol for Indian markets.

        Args:
            symbol: Raw symbol

        Returns:
            Formatted symbol with .NS suffix for NSE
        """
        symbol = symbol.upper().strip()
        # Remove existing exchange suffix
        for suffix in [".NS", ".BO", "-EQ", "-BE"]:
            symbol = symbol.replace(suffix, "")
        return f"{symbol}.NS"

    @abstractmethod
    async def get_fundamentals(self, symbol: str) -> Optional[FundamentalData]:
        """Get fundamental metrics for a stock.

        Args:
            symbol: Stock symbol

        Returns:
            FundamentalData object or None if not found
        """
        pass

    @abstractmethod
    async def refresh_fundamentals(self, symbol: str) -> Optional[FundamentalData]:
        """Force refresh fundamental metrics from source, bypassing cache.

        Args:
            symbol: Stock symbol

        Returns:
            FundamentalData object or None if not found
        """
        pass
