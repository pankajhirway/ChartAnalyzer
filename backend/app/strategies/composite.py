"""Composite Strategy - Combines all trading strategies."""

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from app.models.analysis import StrategyScores, SignalType, ConvictionLevel
from app.strategies.base import BaseStrategy, StrategyResult
from app.strategies.minervini import MinerviniStrategy
from app.strategies.weinstein import WeinsteinStrategy
from app.strategies.lynch import LynchStrategy


@dataclass
class CompositeResult:
    """Result from composite strategy analysis."""
    scores: StrategyScores
    signal: SignalType
    conviction: ConvictionLevel
    bullish_factors: list[str]
    bearish_factors: list[str]
    warnings: list[str]
    strategy_details: dict


class CompositeStrategy:
    """Composite Strategy combining all trading strategies.

    Weighting:
    - Minervini SEPA: 35%
    - Weinstein Stage Analysis: 35%
    - Lynch GARP: 15%
    - Technical Score: 15%

    Signal thresholds:
    - Bullish: composite_score >= 70
    - Neutral: 40 <= composite_score < 70
    - Bearish: composite_score < 40
    """

    WEIGHTS = {
        "minervini": 0.35,
        "weinstein": 0.35,
        "lynch": 0.15,
        "technical": 0.15,
    }

    def __init__(self):
        """Initialize composite strategy with sub-strategies."""
        self.minervini = MinerviniStrategy()
        self.weinstein = WeinsteinStrategy()
        self.lynch = LynchStrategy()

    def analyze(
        self,
        df: pd.DataFrame,
        indicators: dict,
        technical_score: Optional[float] = None,
    ) -> CompositeResult:
        """Run all strategies and combine results.

        Args:
            df: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators
            technical_score: Optional pre-calculated technical score

        Returns:
            CompositeResult with combined analysis
        """
        # Run individual strategies
        minervini_result = self.minervini.analyze(df, indicators)
        weinstein_result = self.weinstein.analyze(df, indicators)
        lynch_result = self.lynch.analyze(df, indicators)

        # Calculate technical score if not provided
        if technical_score is None:
            technical_score = self._calculate_technical_score(df, indicators)

        # Calculate weighted composite score
        composite_score = (
            minervini_result.score * self.WEIGHTS["minervini"] +
            weinstein_result.score * self.WEIGHTS["weinstein"] +
            lynch_result.score * self.WEIGHTS["lynch"] +
            technical_score * self.WEIGHTS["technical"]
        )

        # Create scores object
        scores = StrategyScores(
            minervini_score=round(minervini_result.score, 1),
            weinstein_score=round(weinstein_result.score, 1),
            lynch_score=round(lynch_result.score, 1),
            technical_score=round(technical_score, 1),
            composite_score=round(composite_score, 1),
        )

        # Combine factors
        all_bullish = []
        all_bearish = []
        all_warnings = []

        # Add factors from each strategy with labels
        for factor in minervini_result.bullish_factors[:3]:
            all_bullish.append(f"[Minervini] {factor}")
        for factor in weinstein_result.bullish_factors[:3]:
            all_bullish.append(f"[Weinstein] {factor}")
        for factor in lynch_result.bullish_factors[:3]:
            all_bullish.append(f"[Lynch] {factor}")

        for factor in minervini_result.bearish_factors[:2]:
            all_bearish.append(f"[Minervini] {factor}")
        for factor in weinstein_result.bearish_factors[:2]:
            all_bearish.append(f"[Weinstein] {factor}")
        for factor in lynch_result.bearish_factors[:2]:
            all_bearish.append(f"[Lynch] {factor}")

        for warning in minervini_result.warnings[:2]:
            all_warnings.append(f"[Minervini] {warning}")
        for warning in weinstein_result.warnings[:2]:
            all_warnings.append(f"[Weinstein] {warning}")
        for warning in lynch_result.warnings[:2]:
            all_warnings.append(f"[Lynch] {warning}")

        # Determine signal and conviction
        signal, conviction = self._determine_signal(composite_score, scores)

        # Store strategy details
        strategy_details = {
            "minervini": {
                "score": minervini_result.score,
                "signal": minervini_result.signal,
                "conviction": minervini_result.conviction,
            },
            "weinstein": {
                "score": weinstein_result.score,
                "signal": weinstein_result.signal,
                "conviction": weinstein_result.conviction,
            },
            "lynch": {
                "score": lynch_result.score,
                "signal": lynch_result.signal,
                "conviction": lynch_result.conviction,
            },
            "technical": {
                "score": technical_score,
            },
        }

        return CompositeResult(
            scores=scores,
            signal=signal,
            conviction=conviction,
            bullish_factors=all_bullish,
            bearish_factors=all_bearish,
            warnings=all_warnings,
            strategy_details=strategy_details,
        )

    def _calculate_technical_score(self, df: pd.DataFrame, indicators: dict) -> float:
        """Calculate a pure technical score based on indicators.

        This evaluates technical conditions without strategy bias.
        """
        if df.empty or not indicators:
            return 0.0

        score = 50.0  # Start at neutral
        close = df["close"]
        current_price = float(close.iloc[-1])

        # MA alignment (up to 20 points)
        sma_20 = self._safe_get(indicators, "sma_20")
        sma_50 = self._safe_get(indicators, "sma_50")
        sma_200 = self._safe_get(indicators, "sma_200")

        if sma_20 and current_price > sma_20:
            score += 5
        if sma_50 and current_price > sma_50:
            score += 5
        if sma_200 and current_price > sma_200:
            score += 5
        if sma_20 and sma_50 and sma_20 > sma_50:
            score += 5

        # Momentum indicators (up to 15 points)
        rsi = self._safe_get(indicators, "rsi_14")
        if rsi:
            if 40 < rsi < 70:
                score += 5
            elif rsi > 70:
                score -= 3
            elif rsi < 30:
                score += 3  # Potential bounce

        macd = self._safe_get(indicators, "macd")
        macd_signal = self._safe_get(indicators, "macd_signal")
        if macd and macd_signal:
            if macd > macd_signal:
                score += 5
            else:
                score -= 5

        stoch_k = self._safe_get(indicators, "stoch_k")
        if stoch_k:
            if 20 < stoch_k < 80:
                score += 5

        # Trend strength (up to 10 points)
        adx = self._safe_get(indicators, "adx_14")
        if adx:
            if adx > 25:
                plus_di = self._safe_get(indicators, "plus_di")
                minus_di = self._safe_get(indicators, "minus_di")
                if plus_di and minus_di:
                    if plus_di > minus_di:
                        score += 10
                    else:
                        score -= 5

        # Bollinger Bands position (up to 5 points)
        bb_upper = self._safe_get(indicators, "bb_upper")
        bb_lower = self._safe_get(indicators, "bb_lower")
        if bb_upper and bb_lower:
            bb_mid = (bb_upper + bb_lower) / 2
            if current_price > bb_mid:
                score += 3
            if current_price > bb_upper:
                score -= 3  # Extended
            elif current_price < bb_lower:
                score += 3  # Oversold

        return max(0, min(100, score))

    def _determine_signal(
        self,
        composite_score: float,
        scores: StrategyScores,
    ) -> tuple[SignalType, ConvictionLevel]:
        """Determine overall signal and conviction from composite score."""
        # Check for strong agreement between strategies
        strategy_scores = [
            scores.minervini_score,
            scores.weinstein_score,
            scores.lynch_score or 50,
        ]

        avg_score = sum(strategy_scores) / len(strategy_scores)
        score_std = (sum((s - avg_score) ** 2 for s in strategy_scores) / len(strategy_scores)) ** 0.5

        # Agreement level affects conviction
        agreement = score_std < 15  # Low standard deviation = high agreement

        if composite_score >= 70:
            signal = SignalType.BUY
            if composite_score >= 85 and agreement:
                conviction = ConvictionLevel.HIGH
            else:
                conviction = ConvictionLevel.MEDIUM

        elif composite_score >= 50:
            signal = SignalType.HOLD
            conviction = ConvictionLevel.LOW

        elif composite_score >= 35:
            signal = SignalType.HOLD
            conviction = ConvictionLevel.LOW

        else:
            signal = SignalType.AVOID
            if composite_score < 25 and agreement:
                conviction = ConvictionLevel.HIGH
            else:
                conviction = ConvictionLevel.MEDIUM

        return signal, conviction

    def _safe_get(self, data: dict, key: str, default: any = None) -> any:
        """Safely get value from dictionary."""
        return data.get(key, default) if data else default

    def get_strategy_summary(self, result: CompositeResult) -> str:
        """Generate a text summary of the strategy analysis."""
        lines = [
            f"Composite Score: {result.scores.composite_score:.1f}/100",
            f"Signal: {result.signal.value} ({result.conviction.value})",
            "",
            "Individual Scores:",
            f"  - Minervini SEPA: {result.scores.minervini_score:.1f}",
            f"  - Weinstein Stage: {result.scores.weinstein_score:.1f}",
            f"  - Lynch GARP: {result.scores.lynch_score:.1f}",
            f"  - Technical: {result.scores.technical_score:.1f}",
        ]

        if result.bullish_factors:
            lines.append("")
            lines.append("Bullish Factors:")
            for factor in result.bullish_factors[:5]:
                lines.append(f"  + {factor}")

        if result.bearish_factors:
            lines.append("")
            lines.append("Bearish Factors:")
            for factor in result.bearish_factors[:5]:
                lines.append(f"  - {factor}")

        if result.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in result.warnings[:3]:
                lines.append(f"  ! {warning}")

        return "\n".join(lines)
