"""Zerodha Kite data provider implementation."""

from datetime import datetime, timedelta
from typing import Optional
import asyncio

import structlog

from app.config import get_settings
from app.core.data_provider import DataProvider
from app.models.stock import Stock, PriceData, StockQuote, StockSearchResult, Exchange

logger = structlog.get_logger()
settings = get_settings()


class KiteProvider(DataProvider):
    """Zerodha Kite implementation of data provider.

    Requires Kite Connect API credentials.
    Provides real-time data and extended historical data for Indian markets.
    """

    # Timeframe mapping for Kite
    TIMEFRAME_MAP = {
        "1m": "minute",
        "5m": "5minute",
        "15m": "15minute",
        "30m": "30minute",
        "1h": "60minute",
        "1d": "day",
        "1w": "week",
        "1M": "month",
    }

    def __init__(self):
        """Initialize Kite provider."""
        self._kite = None
        self._initialized = False
        self._instrument_cache: dict[str, int] = {}  # symbol -> instrument_token

    async def _ensure_initialized(self) -> bool:
        """Ensure Kite connection is initialized."""
        if self._initialized:
            return self._kite is not None

        if not all([settings.kite_api_key, settings.kite_api_secret, settings.kite_access_token]):
            logger.warning("Kite credentials not configured, using fallback")
            self._initialized = True
            return False

        try:
            from kiteconnect import KiteConnect

            self._kite = KiteConnect(
                api_key=settings.kite_api_key,
                access_token=settings.kite_access_token,
            )

            # Test connection
            self._kite.profile()
            await self._load_instruments()
            self._initialized = True
            logger.info("Kite provider initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize Kite provider", error=str(e))
            self._initialized = True
            return False

    async def _load_instruments(self) -> None:
        """Load and cache instrument list."""
        if not self._kite:
            return

        try:
            # Run in thread pool since kite is synchronous
            loop = asyncio.get_event_loop()
            instruments = await loop.run_in_executor(
                None,
                lambda: self._kite.instruments("NSE")
            )

            for inst in instruments:
                if inst["segment"] == "NSE" and inst["instrument_type"] == "EQ":
                    symbol = inst["tradingsymbol"]
                    self._instrument_cache[symbol] = inst["instrument_token"]

            logger.info("Loaded instruments", count=len(self._instrument_cache))

        except Exception as e:
            logger.error("Failed to load instruments", error=str(e))

    def _get_instrument_token(self, symbol: str) -> Optional[int]:
        """Get instrument token for a symbol."""
        symbol = symbol.upper().replace(".NS", "").replace(".BO", "")
        return self._instrument_cache.get(symbol)

    async def get_stock_info(self, symbol: str) -> Optional[Stock]:
        """Get stock information by symbol."""
        if not await self._ensure_initialized():
            return None

        try:
            # Kite doesn't provide detailed company info
            # Return basic info from instruments cache
            token = self._get_instrument_token(symbol)
            if not token:
                return None

            return Stock(
                symbol=symbol.upper(),
                company_name=symbol.upper(),  # Kite doesn't provide company names directly
                exchange=Exchange.NSE,
            )

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
        if not await self._ensure_initialized():
            return []

        token = self._get_instrument_token(symbol)
        if not token:
            logger.warning("Instrument not found", symbol=symbol)
            return []

        if not start_date:
            start_date = datetime.now() - timedelta(days=730)
        if not end_date:
            end_date = datetime.now()

        try:
            interval = self.TIMEFRAME_MAP.get(timeframe, "day")
            loop = asyncio.get_event_loop()

            data = await loop.run_in_executor(
                None,
                lambda: self._kite.historical_data(
                    token,
                    from_date=start_date,
                    to_date=end_date,
                    interval=interval,
                )
            )

            result = []
            for item in data:
                price_data = PriceData(
                    symbol=symbol.upper(),
                    timestamp=datetime.fromisoformat(str(item["date"])),
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=int(item["volume"]),
                )
                result.append(price_data)

            return result

        except Exception as e:
            logger.error("Failed to get historical data", symbol=symbol, error=str(e))
            return []

    async def get_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get real-time quote for a stock."""
        if not await self._ensure_initialized():
            return None

        token = self._get_instrument_token(symbol)
        if not token:
            return None

        try:
            loop = asyncio.get_event_loop()
            quote_data = await loop.run_in_executor(
                None,
                lambda: self._kite.quote([token])
            )

            if not quote_data or str(token) not in quote_data:
                return None

            q = quote_data[str(token)]

            change = q["last_price"] - q["ohlc"]["close"]
            change_pct = (change / q["ohlc"]["close"]) * 100 if q["ohlc"]["close"] else 0

            return StockQuote(
                symbol=symbol.upper(),
                last_price=float(q["last_price"]),
                change=float(change),
                change_percent=float(change_pct),
                day_high=float(q["ohlc"]["high"]),
                day_low=float(q["ohlc"]["low"]),
                day_open=float(q["ohlc"]["open"]),
                prev_close=float(q["ohlc"]["close"]),
                volume=int(q.get("volume", 0)),
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error("Failed to get quote", symbol=symbol, error=str(e))
            return None

    async def search_stocks(self, query: str, limit: int = 10) -> list[StockSearchResult]:
        """Search for stocks by name or symbol."""
        if not await self._ensure_initialized():
            return []

        query_lower = query.lower()
        results = []

        for symbol in self._instrument_cache.keys():
            if query_lower in symbol.lower():
                results.append(
                    StockSearchResult(
                        symbol=symbol,
                        company_name=symbol,
                        exchange=Exchange.NSE,
                    )
                )
                if len(results) >= limit:
                    break

        return results

    async def get_multiple_quotes(self, symbols: list[str]) -> dict[str, StockQuote]:
        """Get quotes for multiple stocks."""
        if not await self._ensure_initialized():
            return {}

        tokens = []
        symbol_map = {}

        for symbol in symbols:
            token = self._get_instrument_token(symbol)
            if token:
                tokens.append(token)
                symbol_map[token] = symbol

        if not tokens:
            return {}

        try:
            loop = asyncio.get_event_loop()
            quotes_data = await loop.run_in_executor(
                None,
                lambda: self._kite.quote(tokens)
            )

            results = {}
            for token_str, q in quotes_data.items():
                token = int(token_str)
                symbol = symbol_map.get(token)
                if symbol:
                    change = q["last_price"] - q["ohlc"]["close"]
                    change_pct = (change / q["ohlc"]["close"]) * 100 if q["ohlc"]["close"] else 0

                    results[symbol.upper()] = StockQuote(
                        symbol=symbol.upper(),
                        last_price=float(q["last_price"]),
                        change=float(change),
                        change_percent=float(change_pct),
                        day_high=float(q["ohlc"]["high"]),
                        day_low=float(q["ohlc"]["low"]),
                        day_open=float(q["ohlc"]["open"]),
                        prev_close=float(q["ohlc"]["close"]),
                        volume=int(q.get("volume", 0)),
                        timestamp=datetime.now(),
                    )

            return results

        except Exception as e:
            logger.error("Failed to get multiple quotes", error=str(e))
            return {}
