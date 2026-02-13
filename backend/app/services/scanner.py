"""Market scanner service."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import structlog

from app.core.yfinance_provider import YFinanceProvider
from app.services.analyzer import AnalyzerService
from app.models.analysis import SignalType, ConvictionLevel, AnalysisResult
from app.utils.constants import INDEX_CONSTITUENTS, get_index_constituents

logger = structlog.get_logger()


@dataclass
class ScanFilter:
    """Filter criteria for market scan."""
    min_composite_score: float = 50.0
    max_composite_score: float = 100.0
    signal: Optional[str] = None  # BUY, SELL, HOLD, AVOID
    min_conviction: Optional[str] = None  # HIGH, MEDIUM, LOW
    min_volume_ratio: Optional[float] = None
    trend: Optional[str] = None  # BULLISH, BEARISH, NEUTRAL
    weinstein_stage: Optional[int] = None  # 1, 2, 3, 4


@dataclass
class ScanResult:
    """Result from a market scan."""
    symbol: str
    company_name: Optional[str]
    current_price: float
    composite_score: float
    signal: SignalType
    conviction: ConvictionLevel
    trend: str
    weinstein_stage: int
    patterns: list[str]
    timestamp: datetime


class ScannerService:
    """Service for scanning the market for trade opportunities."""

    def __init__(self):
        """Initialize scanner service."""
        self.data_provider = YFinanceProvider()
        self.analyzer = AnalyzerService()

    async def scan_universe(
        self,
        universe: str = "nifty50",
        scan_filter: Optional[ScanFilter] = None,
        max_results: int = 20,
    ) -> list[ScanResult]:
        """Scan a universe of stocks for opportunities.

        Args:
            universe: Universe to scan (nifty50, nifty200, etc.)
            scan_filter: Filter criteria
            max_results: Maximum number of results to return

        Returns:
            List of ScanResult objects
        """
        if scan_filter is None:
            scan_filter = ScanFilter()

        # Get symbols for the universe - use function for reliability
        symbols = get_index_constituents(universe)
        if not symbols:
            symbols = get_index_constituents("nifty50")
            logger.warning(f"Universe '{universe}' not found, falling back to nifty50")

        logger.info(
            "Starting market scan",
            universe=universe,
            symbols_count=len(symbols),
        )

        # Run analysis on all symbols (with concurrency limit)
        results = await self._analyze_symbols(symbols, scan_filter)

        # Sort by composite score
        results.sort(key=lambda x: x.composite_score, reverse=True)

        # Return top results
        return results[:max_results]

    async def _analyze_symbols(
        self,
        symbols: list[str],
        scan_filter: ScanFilter,
    ) -> list[ScanResult]:
        """Analyze multiple symbols with concurrency control."""
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        results = []

        async def analyze_one(symbol: str):
            async with semaphore:
                try:
                    analysis = await self.analyzer.analyze(symbol)
                    if analysis:
                        result = self._create_scan_result(analysis)
                        if self._passes_filter(result, scan_filter):
                            return result
                except Exception as e:
                    logger.warning("Analysis failed", symbol=symbol, error=str(e))
                return None

        # Run all analyses concurrently
        tasks = [analyze_one(symbol) for symbol in symbols]
        completed = await asyncio.gather(*tasks)

        # Filter out None results
        results = [r for r in completed if r is not None]

        return results

    def _create_scan_result(self, analysis: AnalysisResult) -> ScanResult:
        """Create a scan result from analysis."""
        pattern_names = [p.pattern_name for p in analysis.detected_patterns[:3]]

        return ScanResult(
            symbol=analysis.symbol,
            company_name=analysis.company_name,
            current_price=analysis.current_price,
            composite_score=analysis.scores.composite_score,
            signal=analysis.signal,
            conviction=analysis.conviction,
            trend=analysis.primary_trend.value,
            weinstein_stage=analysis.weinstein_stage.value,
            patterns=pattern_names,
            timestamp=analysis.timestamp,
        )

    def _passes_filter(self, result: ScanResult, f: ScanFilter) -> bool:
        """Check if result passes the filter criteria."""
        if result.composite_score < f.min_composite_score:
            return False
        if result.composite_score > f.max_composite_score:
            return False

        if f.signal and result.signal.value != f.signal:
            return False

        if f.min_conviction:
            conviction_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
            if conviction_order.get(result.conviction.value, 0) < conviction_order.get(f.min_conviction, 0):
                return False

        if f.trend and result.trend != f.trend:
            return False

        if f.weinstein_stage and result.weinstein_stage != f.weinstein_stage:
            return False

        return True

    async def scan_for_breakouts(
        self,
        universe: str = "nifty50",
        min_volume_ratio: float = 1.5,
    ) -> list[ScanResult]:
        """Scan for stocks breaking out.

        Args:
            universe: Universe to scan
            min_volume_ratio: Minimum volume ratio for breakout confirmation

        Returns:
            List of stocks with breakout patterns
        """
        breakout_filter = ScanFilter(
            min_composite_score=60.0,
            signal="BUY",
            min_volume_ratio=min_volume_ratio,
        )

        return await self.scan_universe(universe, breakout_filter)

    async def scan_stage2_stocks(
        self,
        universe: str = "nifty200",
    ) -> list[ScanResult]:
        """Scan for stocks in Weinstein Stage 2.

        Args:
            universe: Universe to scan

        Returns:
            List of Stage 2 stocks
        """
        stage2_filter = ScanFilter(
            min_composite_score=55.0,
            weinstein_stage=2,
            trend="BULLISH",
        )

        return await self.scan_universe(universe, stage2_filter)

    async def scan_minervini_setups(
        self,
        universe: str = "nifty200",
    ) -> list[ScanResult]:
        """Scan for Minervini-style VCP setups.

        Args:
            universe: Universe to scan

        Returns:
            List of stocks with VCP setups
        """
        vcp_filter = ScanFilter(
            min_composite_score=65.0,
            signal="BUY",
        )

        results = await self.scan_universe(universe, vcp_filter, max_results=30)

        # Further filter for VCP patterns
        vcp_results = []
        for result in results:
            if any("VCP" in p or "Cup" in p for p in result.patterns):
                vcp_results.append(result)

        return vcp_results

    def get_preset_filters(self) -> dict:
        """Get preset filter configurations.

        Returns:
            Dictionary of preset filter names and their configurations
        """
        return {
            "bullish_breakouts": {
                "name": "Bullish Breakouts",
                "description": "Stocks breaking out with volume",
                "filter": {
                    "min_composite_score": 60,
                    "signal": "BUY",
                    "min_volume_ratio": 1.5,
                },
            },
            "stage2_advancing": {
                "name": "Stage 2 Advancing",
                "description": "Stocks in Weinstein Stage 2 uptrend",
                "filter": {
                    "min_composite_score": 55,
                    "weinstein_stage": 2,
                    "trend": "BULLISH",
                },
            },
            "high_conviction": {
                "name": "High Conviction",
                "description": "High conviction buy signals",
                "filter": {
                    "min_composite_score": 70,
                    "signal": "BUY",
                    "min_conviction": "HIGH",
                },
            },
            "vcp_setups": {
                "name": "VCP Setups",
                "description": "Minervini-style VCP formations",
                "filter": {
                    "min_composite_score": 65,
                    "signal": "BUY",
                },
            },
            "pullback_entries": {
                "name": "Pullback Entries",
                "description": "Stocks pulling back to support in uptrend",
                "filter": {
                    "min_composite_score": 50,
                    "max_composite_score": 70,
                    "trend": "BULLISH",
                    "weinstein_stage": 2,
                },
            },
            "avoid_signals": {
                "name": "Avoid Signals",
                "description": "Stocks to avoid or consider shorting",
                "filter": {
                    "max_composite_score": 40,
                    "signal": "AVOID",
                },
            },
        }
