"""Peter Lynch GARP (Growth at Reasonable Price) Strategy.

This implementation uses fundamental metrics (P/E ratio, earnings consistency,
ROE, debt levels) following Peter Lynch's GARP methodology.
"""

from typing import Optional

import pandas as pd

from app.models.fundamental import FundamentalData
from app.services.fundamental_scorer import FundamentalScorer, FundamentalScore
from app.strategies.base import BaseStrategy, StrategyResult


class LynchStrategy(BaseStrategy):
    """Peter Lynch's GARP Approach - Using Fundamental Analysis.

    Key principles:
    1. P/E ratio should be less than growth rate (PEG < 1)
    2. Consistent earnings and revenue growth
    3. High ROE indicates quality management
    4. Low debt-to-equity ensures financial stability
    5. Buy growth at reasonable prices

    Scoring (using FundamentalScorer):
    - P/E Ratio (PEG): 0-25 points
    - Growth Quality (EPS & Revenue): 0-30 points
    - ROE/ROCE: 0-25 points
    - Financial Health (Debt): 0-20 points
    Total: 0-100 points
    """

    name = "Lynch GARP Approach"
    description = "Peter Lynch's growth at reasonable price approach (fundamental analysis)"

    def __init__(self):
        """Initialize Lynch strategy with fundamental scorer."""
        super().__init__()
        self._scorer = FundamentalScorer()

    def analyze(
        self,
        df: pd.DataFrame,
        indicators: dict,
        fundamental_data: Optional[FundamentalData] = None,
    ) -> StrategyResult:
        """Analyze stock using Lynch GARP principles with fundamental data.

        Args:
            df: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators
            fundamental_data: Optional fundamental metrics for GARP analysis

        Returns:
            StrategyResult with score and analysis
        """
        # Require minimum data for analysis
        if df.empty or len(df) < 50:
            return StrategyResult(
                score=0,
                bullish_factors=[],
                bearish_factors=["Insufficient data"],
                warnings=["Need at least 50 bars for analysis"],
                signal="AVOID",
                conviction="LOW"
            )

        # Use fundamental scoring if data is available
        if fundamental_data:
            return self._analyze_with_fundamentals(df, indicators, fundamental_data)

        # Fallback to technical analysis if no fundamental data
        return self._analyze_with_technicals(df, indicators)

    def _analyze_with_fundamentals(
        self,
        df: pd.DataFrame,
        indicators: dict,
        fundamental_data: FundamentalData,
    ) -> StrategyResult:
        """Analyze using fundamental GARP scoring."""
        # Score using fundamental scorer
        fundamental_score: Optional[FundamentalScore] = self._scorer.score(fundamental_data)

        if fundamental_score is None:
            # Fundamental data insufficient, fall back to technical
            return self._analyze_with_technicals(df, indicators)

        # Determine signal and conviction from fundamental score
        signal, conviction = self._get_signal_from_score(fundamental_score.score)

        # Add technical context if available
        warnings = list(fundamental_score.warnings)

        # Check if technicals support fundamentals
        technical_notes = self._get_technical_context(df, indicators)
        if technical_notes:
            warnings.extend(technical_notes)

        return StrategyResult(
            score=fundamental_score.score,
            bullish_factors=fundamental_score.bullish_factors,
            bearish_factors=fundamental_score.bearish_factors,
            warnings=warnings,
            signal=signal,
            conviction=conviction
        )

    def _analyze_with_technicals(
        self,
        df: pd.DataFrame,
        indicators: dict,
    ) -> StrategyResult:
        """Fallback technical analysis when fundamental data unavailable."""
        bullish_factors = []
        bearish_factors = []
        warnings = []

        score = 40.0  # Start at neutral for missing fundamentals
        bearish_factors.append("Fundamental data unavailable - using technical fallback")

        # Basic trend assessment
        close = df["close"]
        sma_200 = self._safe_get(indicators, "sma_200")
        sma_50 = self._safe_get(indicators, "sma_50")

        if sma_200:
            if close.iloc[-1] > sma_200:
                score += 15
                bullish_factors.append("Trading above 200-day MA")
            else:
                score -= 10
                bearish_factors.append("Below 200-day MA")

        if sma_50:
            if close.iloc[-1] > sma_50:
                score += 10
                bullish_factors.append("Trading above 50-day MA")

        # RSI momentum
        rsi = self._safe_get(indicators, "rsi_14")
        if rsi:
            if 40 < rsi < 70:
                score += 10
                bullish_factors.append(f"RSI in healthy zone ({rsi:.1f})")
            elif rsi > 70:
                warnings.append(f"RSI overbought ({rsi:.1f})")
            elif rsi < 30:
                score += 5
                bullish_factors.append(f"RSI oversold ({rsi:.1f})")

        warnings.append("Fundamental analysis recommended for accurate GARP scoring")

        signal, conviction = self._get_signal_from_score(max(0, min(100, score)))

        return StrategyResult(
            score=max(0, min(100, score)),
            bullish_factors=bullish_factors,
            bearish_factors=bearish_factors,
            warnings=warnings,
            signal=signal,
            conviction=conviction
        )

    def _get_technical_context(
        self,
        df: pd.DataFrame,
        indicators: dict,
    ) -> list[str]:
        """Get technical context notes for fundamental analysis.

        Returns warnings when technicals don't align with fundamentals.
        """
        notes = []
        close = df["close"]
        current_price = float(close.iloc[-1])

        # Check if price is extended (might not be a good entry)
        sma_50 = self._safe_get(indicators, "sma_50")
        if sma_50:
            distance_pct = ((current_price - sma_50) / sma_50) * 100
            if distance_pct > 15:
                notes.append(f"Price extended {distance_pct:.1f}% above 50-day MA - consider waiting for pullback")
            elif distance_pct < -10:
                notes.append(f"Price below 50-day MA by {distance_pct:.1f}% - technical weakness")

        # Check for overbought conditions
        rsi = self._safe_get(indicators, "rsi_14")
        if rsi and rsi > 75:
            notes.append(f"RSI overbought ({rsi:.1f}) - short-term risk")

        # Check trend alignment
        sma_20 = self._safe_get(indicators, "sma_20")
        sma_50 = self._safe_get(indicators, "sma_50")
        if sma_20 and sma_50:
            if sma_20 < sma_50:
                notes.append("Short-term MA below long-term MA - downtrend concern")

        return notes

    def _get_signal_from_score(self, score: float) -> tuple[str, str]:
        """Determine signal and conviction from score.

        Returns:
            Tuple of (signal, conviction)
        """
        if score >= 80:
            return "BUY", "HIGH"
        elif score >= 65:
            return "BUY", "MEDIUM"
        elif score >= 50:
            return "HOLD", "LOW"
        elif score >= 35:
            return "AVOID", "MEDIUM"
        else:
            return "SELL", "HIGH"

    def _safe_get(self, data: dict, key: str, default: any = None) -> any:
        """Safely get value from dictionary."""
        return data.get(key, default) if data else default
