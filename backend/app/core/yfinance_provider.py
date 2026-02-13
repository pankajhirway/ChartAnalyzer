"""Yahoo Finance data provider implementation."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import yfinance as yf
import pandas as pd
import structlog

from app.core.data_provider import DataProvider
from app.models.stock import Stock, PriceData, StockQuote, StockSearchResult, Exchange

logger = structlog.get_logger()


class YFinanceProvider(DataProvider):
    """Yahoo Finance implementation of data provider.

    Uses yfinance library to fetch Indian stock data from Yahoo Finance.
    Symbols should be formatted with .NS suffix for NSE or .BO for BSE.
    """

    # Mapping of common Indian stock symbols
    SYMBOL_MAPPING = {
        "NIFTY50": "^NSEI",
        "NIFTY": "^NSEI",
        "SENSEX": "^BSESN",
        "BANKNIFTY": "^NSEBANK",
    }

    # Timeframe mapping for yfinance
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "60m",
        "1d": "1d",
        "1w": "1wk",
        "1M": "1mo",
    }

    def __init__(self):
        """Initialize YFinance provider."""
        self._cache: dict[str, tuple[datetime, any]] = {}
        self._cache_ttl = 300  # 5 minutes

    def _get_cached(self, key: str) -> Optional[any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            timestamp, value = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                return value
        return None

    def _set_cache(self, key: str, value: any) -> None:
        """Set value in cache."""
        self._cache[key] = (datetime.now(), value)

    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for yfinance.

        Args:
            symbol: Raw symbol (e.g., "RELIANCE" or "RELIANCE.NS")

        Returns:
            Formatted symbol for yfinance
        """
        symbol = symbol.upper().strip()

        # Check if it's a known index
        if symbol in self.SYMBOL_MAPPING:
            return self.SYMBOL_MAPPING[symbol]

        # Remove existing exchange suffix
        for suffix in [".NS", ".BO", "-EQ", "-BE"]:
            symbol = symbol.replace(suffix, "")

        # Default to NSE
        return f"{symbol}.NS"

    async def get_stock_info(self, symbol: str) -> Optional[Stock]:
        """Get stock information by symbol."""
        formatted_symbol = self._format_symbol(symbol)
        cache_key = f"info_{formatted_symbol}"

        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            ticker = yf.Ticker(formatted_symbol)
            info = ticker.info

            if not info:
                return None

            # Determine exchange from symbol
            exchange = Exchange.NSE
            if ".BO" in formatted_symbol:
                exchange = Exchange.BSE

            stock = Stock(
                symbol=symbol.upper().replace(".NS", "").replace(".BO", ""),
                company_name=info.get("longName", info.get("shortName", symbol)),
                exchange=exchange,
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=info.get("marketCap", 0) / 10000000 if info.get("marketCap") else None,  # Convert to crores
                isin=info.get("isin"),
                face_value=info.get("faceValue"),
            )

            self._set_cache(cache_key, stock)
            return stock

        except Exception as e:
            logger.error("Failed to get stock info", symbol=symbol, error=str(e))
            return None

    async def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = "1d",
    ) -> list[PriceData]:
        """Get historical price data."""
        formatted_symbol = self._format_symbol(symbol)

        if not start_date:
            start_date = datetime.now() - timedelta(days=730)  # 2 years
        if not end_date:
            end_date = datetime.now()

        try:
            ticker = yf.Ticker(formatted_symbol)

            # Map timeframe
            interval = self.TIMEFRAME_MAP.get(timeframe, "1d")

            # For intraday data, limit the period
            period = None
            if interval in ["1m", "5m", "15m", "30m", "60m"]:
                # Intraday data is limited to last 60 days
                start_date = max(start_date, datetime.now() - timedelta(days=59))

            # Fetch data
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=False,
            )

            if df.empty:
                return []

            # Convert to PriceData list
            result = []
            for index, row in df.iterrows():
                price_data = PriceData(
                    symbol=symbol.upper().replace(".NS", "").replace(".BO", ""),
                    timestamp=index.to_pydatetime(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                    adj_close=float(row.get("Adj Close", row["Close"])),
                )
                result.append(price_data)

            return result

        except Exception as e:
            logger.error("Failed to get historical data", symbol=symbol, error=str(e))
            return []

    async def get_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get real-time quote for a stock."""
        formatted_symbol = self._format_symbol(symbol)
        cache_key = f"quote_{formatted_symbol}"

        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            ticker = yf.Ticker(formatted_symbol)

            # Get fast info for real-time data
            fast_info = ticker.fast_info
            info = ticker.info

            if not fast_info:
                return None

            current_price = fast_info.last_price or info.get("currentPrice")
            prev_close = fast_info.previous_close or info.get("previousClose")

            if current_price is None or prev_close is None:
                return None

            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close else 0

            quote = StockQuote(
                symbol=symbol.upper().replace(".NS", "").replace(".BO", ""),
                company_name=info.get("longName", info.get("shortName")),
                last_price=float(current_price),
                change=float(change),
                change_percent=float(change_percent),
                day_high=float(fast_info.day_high or info.get("dayHigh", current_price)),
                day_low=float(fast_info.day_low or info.get("dayLow", current_price)),
                day_open=float(fast_info.open or info.get("openPrice", current_price)),
                prev_close=float(prev_close),
                volume=int(fast_info.last_volume or info.get("volume", 0)),
                avg_volume=int(info.get("averageVolume", 0)),
                fifty_two_week_high=float(fast_info.year_high or info.get("fiftyTwoWeekHigh", 0)),
                fifty_two_week_low=float(fast_info.year_low or info.get("fiftyTwoWeekLow", 0)),
                timestamp=datetime.now(),
            )

            self._set_cache(cache_key, quote)
            return quote

        except Exception as e:
            logger.error("Failed to get quote", symbol=symbol, error=str(e))
            return None

    async def search_stocks(self, query: str, limit: int = 10) -> list[StockSearchResult]:
        """Search for stocks by name or symbol."""
        try:
            # yfinance doesn't have a direct search, we'll use a predefined list
            # and filter based on query
            from app.utils.constants import NSE_STOCKS

            query_lower = query.lower()
            results = []

            for stock in NSE_STOCKS:
                if (
                    query_lower in stock["symbol"].lower()
                    or query_lower in stock["name"].lower()
                ):
                    results.append(
                        StockSearchResult(
                            symbol=stock["symbol"],
                            company_name=stock["name"],
                            exchange=Exchange.NSE,
                            sector=stock.get("sector"),
                        )
                    )
                    if len(results) >= limit:
                        break

            return results

        except Exception as e:
            logger.error("Failed to search stocks", query=query, error=str(e))
            return []

    async def get_multiple_quotes(self, symbols: list[str]) -> dict[str, StockQuote]:
        """Get quotes for multiple stocks."""
        results = {}

        # Process in parallel with rate limiting
        tasks = [self.get_quote(symbol) for symbol in symbols]
        quotes = await asyncio.gather(*tasks)

        for symbol, quote in zip(symbols, quotes):
            if quote:
                results[symbol.upper()] = quote

        return results

    async def get_index_constituents(self, index: str = "nifty50") -> list[str]:
        """Get list of stocks in an index.

        Args:
            index: Index name (nifty50, nifty100, etc.)

        Returns:
            List of stock symbols
        """
        from app.utils.constants import INDEX_CONSTITUENTS

        return INDEX_CONSTITUENTS.get(index, INDEX_CONSTITUENTS["nifty50"])
