"""Market scanner service."""

import asyncio
import uuid
from dataclasses import dataclass, field
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
    # Fundamental filters
    min_pe: Optional[float] = None
    max_pe: Optional[float] = None
    min_roe: Optional[float] = None
    max_debt_to_equity: Optional[float] = None
    min_growth: Optional[float] = None  # Minimum EPS or revenue growth (%)


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
    volume: int = 0
    avg_volume: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ScanProgress:
    """Progress tracking for a scan operation."""
    scan_id: str
    status: str  # pending, in_progress, completed, failed
    current: int = 0
    total: int = 0
    results_found: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    timestamp: datetime
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None
    eps_growth: Optional[float] = None
    revenue_growth: Optional[float] = None


class ScannerService:
    """Service for scanning the market for trade opportunities."""

    def __init__(self):
        """Initialize scanner service."""
        self.data_provider = YFinanceProvider()
        self.analyzer = AnalyzerService()
        self._scan_progress: dict[str, ScanProgress] = {}

    def get_scan_progress(self, scan_id: str) -> Optional[ScanProgress]:
        """Get progress of a scan by its ID.

        Args:
            scan_id: Unique identifier for the scan

        Returns:
            ScanProgress object if found, None otherwise
        """
        return self._scan_progress.get(scan_id)

    async def scan_universe(
        self,
        universe: str = "nifty50",
        scan_filter: Optional[ScanFilter] = None,
        max_results: int = 20,
        scan_id: Optional[str] = None,
    ) -> list[ScanResult]:
        """Scan a universe of stocks for opportunities.

        Args:
            universe: Universe to scan (nifty50, nifty200, etc.)
            scan_filter: Filter criteria
            max_results: Maximum number of results to return
            scan_id: Optional scan ID for progress tracking

        Returns:
            List of ScanResult objects
        """
        if scan_filter is None:
            scan_filter = ScanFilter()

        # Generate scan ID if not provided
        if scan_id is None:
            scan_id = str(uuid.uuid4())

        # Get symbols for the universe - use function for reliability
        symbols = get_index_constituents(universe)
        if not symbols:
            symbols = get_index_constituents("nifty50")
            logger.warning(f"Universe '{universe}' not found, falling back to nifty50")

        # Initialize progress tracking
        progress = ScanProgress(
            scan_id=scan_id,
            status="in_progress",
            total=len(symbols),
            started_at=datetime.now(),
        )
        self._scan_progress[scan_id] = progress

        logger.info(
            "Starting market scan",
            scan_id=scan_id,
            universe=universe,
            symbols_count=len(symbols),
        )

        # Run analysis on all symbols (with concurrency limit)
        results = await self._analyze_symbols(symbols, scan_filter, scan_id)

        # Update progress as completed
        progress.status = "completed"
        progress.current = len(symbols)
        progress.results_found = len(results)
        progress.completed_at = datetime.now()

        # Sort by composite score
        results.sort(key=lambda x: x.composite_score, reverse=True)

        # Return top results
        return results[:max_results]

    async def _analyze_symbols(
        self,
        symbols: list[str],
        scan_filter: ScanFilter,
        scan_id: str,
    ) -> list[ScanResult]:
        """Analyze multiple symbols with concurrency control."""
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        results = []
        progress = self._scan_progress.get(scan_id)
        processed_count = 0

        async def analyze_one(symbol: str):
            nonlocal processed_count
            async with semaphore:
                try:
                    analysis = await self.analyzer.analyze(symbol)
                    if analysis:
                        result = await self._create_scan_result(analysis)
                        if self._passes_filter(result, scan_filter):
                            return result
                except Exception as e:
                    logger.warning("Analysis failed", symbol=symbol, error=str(e))
                finally:
                    # Update progress
                    processed_count += 1
                    if progress:
                        progress.current = processed_count
                return None

        # Run all analyses concurrently
        tasks = [analyze_one(symbol) for symbol in symbols]
        completed = await asyncio.gather(*tasks)

        # Filter out None results
        results = [r for r in completed if r is not None]

        return results

    async def _create_scan_result(self, analysis: AnalysisResult) -> ScanResult:
        """Create a scan result from analysis."""
        pattern_names = [p.pattern_name for p in analysis.detected_patterns[:3]]

        # Try to get current quote for volume data
        volume = 0
        avg_volume = 0
        try:
            quote = await self.data_provider.get_quote(analysis.symbol)
            if quote:
                volume = quote.volume
                avg_volume = quote.avg_volume or 0
        except Exception:
            pass  # Volume data is optional, continue without it
        # Extract fundamental data if available
        pe_ratio = None
        pb_ratio = None
        roe = None
        debt_to_equity = None
        eps_growth = None
        revenue_growth = None

        if analysis.fundamental_data:
            pe_ratio = analysis.fundamental_data.pe_ratio
            pb_ratio = analysis.fundamental_data.pb_ratio
            roe = analysis.fundamental_data.roe
            debt_to_equity = analysis.fundamental_data.debt_to_equity
            eps_growth = analysis.fundamental_data.eps_growth
            revenue_growth = analysis.fundamental_data.revenue_growth

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
            volume=volume,
            avg_volume=avg_volume,
            timestamp=analysis.timestamp,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            roe=roe,
            debt_to_equity=debt_to_equity,
            eps_growth=eps_growth,
            revenue_growth=revenue_growth,
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

        if f.min_volume_ratio and result.avg_volume > 0:
            volume_ratio = result.volume / result.avg_volume
            if volume_ratio < f.min_volume_ratio:
        # Fundamental filters
        if f.min_pe is not None:
            if result.pe_ratio is None or result.pe_ratio < f.min_pe:
                return False

        if f.max_pe is not None:
            if result.pe_ratio is None or result.pe_ratio > f.max_pe:
                return False

        if f.min_roe is not None:
            if result.roe is None or result.roe < f.min_roe:
                return False

        if f.max_debt_to_equity is not None:
            if result.debt_to_equity is None or result.debt_to_equity > f.max_debt_to_equity:
                return False

        if f.min_growth is not None:
            # Check both EPS and revenue growth - at least one must meet the minimum
            eps_ok = result.eps_growth is not None and result.eps_growth >= f.min_growth
            revenue_ok = result.revenue_growth is not None and result.revenue_growth >= f.min_growth
            if not (eps_ok or revenue_ok):
                return False

        return True

    async def scan_for_breakouts(
        self,
        universe: str = "nifty50",
        min_volume_ratio: float = 1.5,
        scan_id: Optional[str] = None,
    ) -> list[ScanResult]:
        """Scan for stocks breaking out.

        Args:
            universe: Universe to scan
            min_volume_ratio: Minimum volume ratio for breakout confirmation
            scan_id: Optional scan ID for progress tracking

        Returns:
            List of stocks with breakout patterns
        """
        breakout_filter = ScanFilter(
            min_composite_score=60.0,
            signal="BUY",
            min_volume_ratio=min_volume_ratio,
        )

        return await self.scan_universe(universe, breakout_filter, scan_id=scan_id)

    async def scan_stage2_stocks(
        self,
        universe: str = "nifty200",
        scan_id: Optional[str] = None,
    ) -> list[ScanResult]:
        """Scan for stocks in Weinstein Stage 2.

        Args:
            universe: Universe to scan
            scan_id: Optional scan ID for progress tracking

        Returns:
            List of Stage 2 stocks
        """
        stage2_filter = ScanFilter(
            min_composite_score=55.0,
            weinstein_stage=2,
            trend="BULLISH",
        )

        return await self.scan_universe(universe, stage2_filter, scan_id=scan_id)

    async def scan_minervini_setups(
        self,
        universe: str = "nifty200",
        scan_id: Optional[str] = None,
    ) -> list[ScanResult]:
        """Scan for Minervini-style VCP setups.

        Args:
            universe: Universe to scan
            scan_id: Optional scan ID for progress tracking

        Returns:
            List of stocks with VCP setups
        """
        vcp_filter = ScanFilter(
            min_composite_score=65.0,
            signal="BUY",
        )

        results = await self.scan_universe(universe, vcp_filter, max_results=30, scan_id=scan_id)

        # Further filter for VCP patterns
        vcp_results = []
        for result in results:
            if any("VCP" in p or "Cup" in p for p in result.patterns):
                vcp_results.append(result)

        return vcp_results

    def get_preset_filters(self) -> dict:
        """Get preset filter configurations with strategy rationales.

        Returns:
            Dictionary of preset filter names and their configurations including
            descriptions, strategy rationales, and metadata
        """
        return {
            "minervini_breakouts": {
                "id": "minervini_breakouts",
                "name": "Minervini Breakouts",
                "description": "Stocks showing VCP (Volatility Contraction Pattern) or base breakout patterns with volume confirmation",
                "strategy_rationale": (
                    "Based on Mark Minervini's SEPA (Specific Entry Point Analysis) strategy. "
                    "VCP patterns show decreasing volatility as the base forms, indicating supply "
                    "absorption. Breakouts from such patterns, especially with volume confirmation, "
                    "have a high probability of success. The strategy identifies stocks in Stage 2 "
                    "uptrends breaking out of constructive consolidation periods."
                ),
                "filter": {
                    "min_composite_score": 65.0,
                    "signal": "BUY",
                    "min_volume_ratio": 1.2,
                },
                "recommended_universe": "nifty200",
                "holding_period": "SWING",
                "difficulty": "intermediate",
            },
            "stage_2_stocks": {
                "id": "stage_2_stocks",
                "name": "Stage 2 Stocks",
                "description": "Stocks in Weinstein Stage 2 (advancing phase) with strong uptrend characteristics",
                "strategy_rationale": (
                    "Based on Stan Weinstein's stage theory. Stage 2 is the 'advancing' phase where "
                    "stocks break above 30-week moving average and establish higher highs and higher "
                    "lows. This is the optimal time to be long as institutional accumulation typically "
                    "occurs in this phase. Stocks in Stage 2 with bullish trends have historically "
                    "outperformed the market."
                ),
                "filter": {
                    "min_composite_score": 55.0,
                    "trend": "BULLISH",
                    "weinstein_stage": 2,
                },
                "recommended_universe": "nifty200",
                "holding_period": "POSITIONAL",
                "difficulty": "beginner",
            },
            "vcp_setups": {
                "id": "vcp_setups",
                "name": "VCP Setups",
                "description": "Volatility Contraction Pattern setups - tightening price action with decreasing volatility",
                "strategy_rationale": (
                    "VCP is Mark Minervini's signature pattern. It shows successive contractions "
                    "in price range and volume, indicating that sellers are exhausted and supply is "
                    "being absorbed by stronger hands. The pattern typically has 3-5 contractions, "
                    "with each contraction smaller than the previous. As the pattern tightens, the "
                    "stock becomes coiled for a potential explosive move when breakout occurs."
                ),
                "filter": {
                    "min_composite_score": 60.0,
                    "signal": "BUY",
                },
                "recommended_universe": "nifty200",
                "holding_period": "SWING",
                "difficulty": "advanced",
            },
            "high_composite_score": {
                "id": "high_composite_score",
                "name": "High Composite Score",
                "description": "Stocks with highest composite technical scores across all analysis dimensions",
                "strategy_rationale": (
                    "The composite score combines multiple technical indicators, trend strength, "
                    "pattern detection, and strategy alignment into a single metric. High composite "
                    "scores indicate stocks that are performing well across multiple dimensions: "
                    "strong trend, positive momentum, supportive technical indicators, and presence "
                    "of bullish patterns. This multi-factor approach reduces false positives and "
                    "identifies the strongest opportunities."
                ),
                "filter": {
                    "min_composite_score": 75.0,
                    "signal": "BUY",
                    "min_conviction": "MEDIUM",
                },
                "recommended_universe": "nifty200",
                "holding_period": "SWING",
                "difficulty": "beginner",
            },
            "volume_breakouts": {
                "id": "volume_breakouts",
                "name": "Volume Breakouts",
                "description": "Stocks breaking above resistance with significant volume increase (52-week high focus)",
                "strategy_rationale": (
                    "Volume confirms the validity of price movements. A breakout above resistance "
                    "with above-average volume indicates institutional participation and genuine "
                    "accumulation. Stocks hitting 52-week highs with volume often continue higher as "
                    "new buyers enter and short sellers get squeezed. This preset specifically targets "
                    "stocks breaking to new highs with 1.5x or higher average volume."
                ),
                "filter": {
                    "min_composite_score": 60.0,
                    "signal": "BUY",
                    "min_volume_ratio": 1.5,
                },
                "recommended_universe": "nifty200",
                "holding_period": "SWING",
                "difficulty": "beginner",
            },
            "52w_high_vol": {
                "id": "52w_high_vol",
                "name": "52-Week High with Volume",
                "description": "Stocks hitting or approaching 52-week highs with strong volume confirmation",
                "strategy_rationale": (
                    "Stocks making new 52-week highs with volume represent strong momentum plays. "
                    "When a stock breaks to new highs, there's no overhead resistance, and increased "
                    "volume confirms institutional participation. This combination often leads to "
                    "continued upward movement as new buyers enter and short sellers are forced to "
                    "cover. The strategy focuses on high-conviction setups where the composite score "
                    "confirms technical strength alongside the price breakout."
                ),
                "filter": {
                    "min_composite_score": 65.0,
                    "signal": "BUY",
                    "min_volume_ratio": 1.3,
                    "min_conviction": "MEDIUM",
                },
                "recommended_universe": "nifty200",
                "holding_period": "SWING",
                "difficulty": "intermediate",
            },
            "pullback_entries": {
                "id": "pullback_entries",
                "name": "Pullback Entries",
                "description": "Stocks in uptrend pulling back to key moving averages or support zones",
                "strategy_rationale": (
                    "In established uptrends, pullbacks to support areas (like 21-day EMA or 50-day SMA) "
                    "offer favorable risk-reward entry points. Instead of chasing breakouts, this preset "
                    "identifies stocks in Stage 2 that are experiencing temporary weakness within the "
                    "context of a larger uptrend. These pullbacks provide opportunities to enter strong "
                    "stocks at better prices with closer stops."
                ),
                "filter": {
                    "min_composite_score": 50.0,
                    "max_composite_score": 75.0,
                    "trend": "BULLISH",
                    "weinstein_stage": 2,
                },
                "recommended_universe": "nifty200",
                "holding_period": "SWING",
                "difficulty": "intermediate",
            },
            "high_conviction": {
                "id": "high_conviction",
                "name": "High Conviction",
                "description": "High conviction buy signals where multiple indicators and strategies align",
                "strategy_rationale": (
                    "High conviction signals occur when multiple independent analysis methods align: "
                    "Minervini criteria are met, Weinstein Stage 2 is confirmed, multiple bullish patterns "
                    "are detected, and technical indicators are supportive. This convergence reduces "
                    "uncertainty and increases probability of success. These setups are suitable for "
                    "larger position sizes due to higher confidence levels."
                ),
                "filter": {
                    "min_composite_score": 70.0,
                    "signal": "BUY",
                    "min_conviction": "HIGH",
                },
                "recommended_universe": "nifty50",
                "holding_period": "POSITIONAL",
                "difficulty": "beginner",
            },
        }
