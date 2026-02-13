"""Mark Minervini SEPA (Specific Entry Point Analysis) Strategy."""

from typing import Optional

import numpy as np
import pandas as pd

from app.strategies.base import BaseStrategy, StrategyResult


class MinerviniStrategy(BaseStrategy):
    """Mark Minervini's SEPA Strategy Implementation.

    Core principles:
    1. Stock must be in Stage 2 uptrend (Weinstein alignment)
    2. Price > SMA(50) > SMA(150) > SMA(200)
    3. SMA(150) and SMA(200) must be trending up
    4. Current price at least 30% above 52-week low
    5. Current price within 25% of 52-week high
    6. VCP pattern formation
    7. Volume confirmation on breakout
    """

    name = "Minervini SEPA"
    description = "Mark Minervini's Specific Entry Point Analysis strategy"

    def analyze(self, df: pd.DataFrame, indicators: dict) -> StrategyResult:
        """Analyze stock using SEPA criteria.

        Scoring breakdown:
        - Setup Quality: 0-25 points
        - VCP Formation: 0-25 points
        - Volume Analysis: 0-20 points
        - Relative Strength: 0-15 points
        - Market Alignment: 0-15 points
        Total: 0-100 points
        """
        if df.empty or len(df) < 200:
            return StrategyResult(
                score=0,
                bullish_factors=[],
                bearish_factors=["Insufficient data"],
                warnings=["Need at least 200 bars of data"],
                signal="AVOID",
                conviction="LOW"
            )

        bullish_factors = []
        bearish_factors = []
        warnings = []

        # Calculate scores for each component
        setup_score = self._score_setup(df, indicators, bullish_factors, bearish_factors, warnings)
        vcp_score = self._score_vcp(df, indicators, bullish_factors, bearish_factors)
        volume_score = self._score_volume(df, indicators, bullish_factors, bearish_factors)
        rs_score = self._score_relative_strength(df, indicators, bullish_factors, warnings)
        market_score = self._score_market_alignment(df, indicators, bullish_factors, warnings)

        # Total score (weighted)
        total_score = setup_score + vcp_score + volume_score + rs_score + market_score

        signal, conviction = self._get_signal_from_score(total_score)

        return StrategyResult(
            score=total_score,
            bullish_factors=bullish_factors,
            bearish_factors=bearish_factors,
            warnings=warnings,
            signal=signal,
            conviction=conviction
        )

    def _score_setup(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        bearish: list,
        warnings: list,
    ) -> float:
        """Score setup criteria (0-25 points)."""
        score = 0.0
        close = df["close"]
        current_price = float(close.iloc[-1])

        # Check MA alignment
        sma_50 = self._safe_get(indicators, "sma_50")
        sma_150 = self._safe_get(indicators, "sma_150")
        sma_200 = self._safe_get(indicators, "sma_200")

        if sma_50 and sma_150 and sma_200:
            # Price > SMA50 > SMA150 > SMA200
            if current_price > sma_50 > sma_150 > sma_200:
                score += 10
                bullish.append("Perfect MA alignment: Price > SMA50 > SMA150 > SMA200")
            elif current_price > sma_50 > sma_150:
                score += 7
                bullish.append("Good MA alignment: Price > SMA50 > SMA150")
            elif current_price > sma_50:
                score += 3
                bullish.append("Price above SMA50")
            else:
                bearish.append("Price below key moving averages")
                score -= 5

            # Check MA slopes (should be rising)
            if len(close) >= 200:
                sma_150_series = close.rolling(window=150).mean()
                sma_200_series = close.rolling(window=200).mean()

                slope_150 = (sma_150_series.iloc[-1] - sma_150_series.iloc[-20]) / sma_150_series.iloc[-20]
                slope_200 = (sma_200_series.iloc[-1] - sma_200_series.iloc[-20]) / sma_200_series.iloc[-20]

                if slope_150 > 0:
                    score += 3
                    bullish.append("SMA150 trending up")
                else:
                    bearish.append("SMA150 not trending up")

                if slope_200 > 0:
                    score += 2
                    bullish.append("SMA200 trending up")
                else:
                    bearish.append("SMA200 not trending up")

        # Check 52-week range
        year_high = float(close.tail(252).max()) if len(close) >= 252 else float(close.max())
        year_low = float(close.tail(252).min()) if len(close) >= 252 else float(close.min())

        pct_from_low = (current_price - year_low) / year_low * 100
        pct_from_high = (year_high - current_price) / year_high * 100

        if pct_from_low >= 30:
            score += 3
            bullish.append(f"At least 30% above 52-week low ({pct_from_low:.1f}%)")
        else:
            warnings.append(f"Only {pct_from_low:.1f}% above 52-week low (need 30%)")

        if pct_from_high <= 25:
            score += 4
            bullish.append(f"Within 25% of 52-week high ({pct_from_high:.1f}% below)")
        else:
            warnings.append(f"Too far from 52-week high ({pct_from_high:.1f}% below)")

        # Stage 2 requirement (simplified check)
        if sma_50 and current_price > sma_50:
            score += 3

        return max(0, min(25, score))

    def _score_vcp(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        bearish: list,
    ) -> float:
        """Score VCP (Volatility Contraction Pattern) formation (0-25 points)."""
        score = 0.0

        if len(df) < 100:
            return 0

        # Find recent contractions
        lookback = min(100, len(df))
        data = df.tail(lookback)

        high = data["high"]
        low = data["low"]

        # Find swing highs and lows
        pivots = self._find_swings(data, window=5)

        if len(pivots) < 3:
            return 0

        # Analyze contractions
        contractions = []
        for i in range(0, len(pivots) - 1, 2):
            if i + 1 < len(pivots):
                pivot_high = pivots[i]["value"] if pivots[i]["type"] == "high" else pivots[i + 1]["value"]
                pivot_low = pivots[i]["value"] if pivots[i]["type"] == "low" else pivots[i + 1]["value"]

                if pivot_high > pivot_low:
                    contraction = (pivot_high - pivot_low) / pivot_high * 100
                    contractions.append(contraction)

        if not contractions:
            return 0

        # VCP: contractions should be getting smaller
        is_contracting = len(contractions) >= 2 and all(
            contractions[i] > contractions[i + 1]
            for i in range(len(contractions) - 1)
        )

        if is_contracting:
            score += 15
            bullish.append(f"VCP forming with {len(contractions)} contracting waves")
            score += min(10, len(contractions) * 3)  # More contractions = higher score
        elif contractions:
            # Partial VCP
            avg_contraction = sum(contractions) / len(contractions)
            if avg_contraction < 15:  # Tight price action
                score += 8
                bullish.append("Tight price action (potential VCP)")
            else:
                score += 3

        return min(25, score)

    def _score_volume(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        bearish: list,
    ) -> float:
        """Score volume characteristics (0-20 points)."""
        score = 0.0

        if "volume" not in df.columns:
            return 0

        volume = df["volume"]
        close = df["close"]

        # Volume trend
        vol_sma_20 = self._safe_get(indicators, "volume_sma_20")
        current_vol = int(volume.iloc[-1])

        if vol_sma_20:
            vol_ratio = current_vol / vol_sma_20

            if vol_ratio > 1.5:
                score += 8
                bullish.append(f"High volume ({vol_ratio:.1f}x average)")
            elif vol_ratio > 1.0:
                score += 5
                bullish.append("Above average volume")
            elif vol_ratio < 0.5:
                score += 5  # Volume drying up is good for VCP
                bullish.append("Volume drying up (typical for VCP)")
            else:
                score += 2

        # Volume on up vs down days
        recent = df.tail(20)
        up_days = recent[recent["close"] > recent["open"]]
        down_days = recent[recent["close"] < recent["open"]]

        if len(up_days) > 0 and len(down_days) > 0:
            up_vol = up_days["volume"].mean()
            down_vol = down_days["volume"].mean()

            if up_vol > down_vol * 1.3:
                score += 7
                bullish.append("Higher volume on up days (accumulation)")
            elif down_vol > up_vol * 1.3:
                score -= 5
                bearish.append("Higher volume on down days (distribution)")

        return max(0, min(20, score))

    def _score_relative_strength(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        warnings: list,
    ) -> float:
        """Score relative strength (0-15 points)."""
        score = 0.0

        rs = self._safe_get(indicators, "relative_strength")

        if rs is None:
            # Calculate basic RS if not provided
            if len(df) >= 50:
                close = df["close"]
                price_change = close.iloc[-1] / close.iloc[-50] - 1
                # Assume market is flat for estimation
                rs = 1 + price_change

        if rs is not None:
            if rs > 1.2:
                score += 15
                bullish.append(f"Strong relative strength ({rs:.2f}x)")
            elif rs > 1.0:
                score += 10
                bullish.append(f"Positive relative strength ({rs:.2f}x)")
            elif rs > 0.9:
                score += 5
            else:
                warnings.append(f"Weak relative strength ({rs:.2f}x)")

        return min(15, score)

    def _score_market_alignment(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        warnings: list,
    ) -> float:
        """Score market alignment (0-15 points)."""
        score = 0.0

        # Check trend indicators
        adx = self._safe_get(indicators, "adx_14")
        plus_di = self._safe_get(indicators, "plus_di")
        minus_di = self._safe_get(indicators, "minus_di")

        if adx is not None:
            if adx > 25:
                score += 5
                if plus_di and minus_di and plus_di > minus_di:
                    score += 5
                    bullish.append(f"Strong trending market (ADX: {adx:.1f})")
                elif plus_di and minus_di and plus_di < minus_di:
                    score -= 3
                    warnings.append("Stock in downtrend")
            else:
                score += 2

        # MACD alignment
        macd = self._safe_get(indicators, "macd")
        macd_signal = self._safe_get(indicators, "macd_signal")

        if macd is not None and macd_signal is not None:
            if macd > macd_signal and macd > 0:
                score += 5
                bullish.append("MACD bullish")
            elif macd < macd_signal and macd < 0:
                score -= 3
                warnings.append("MACD bearish")

        return max(0, min(15, score))

    def _find_swings(self, df: pd.DataFrame, window: int = 5) -> list[dict]:
        """Find swing highs and lows."""
        swings = []
        high = df["high"]
        low = df["low"]

        for i in range(window, len(df) - window):
            # Swing high
            if all(high.iloc[i] >= high.iloc[i - j] for j in range(1, window + 1)) and \
               all(high.iloc[i] >= high.iloc[i + j] for j in range(1, window + 1)):
                swings.append({"type": "high", "index": i, "value": float(high.iloc[i])})

            # Swing low
            if all(low.iloc[i] <= low.iloc[i - j] for j in range(1, window + 1)) and \
               all(low.iloc[i] <= low.iloc[i + j] for j in range(1, window + 1)):
                swings.append({"type": "low", "index": i, "value": float(low.iloc[i])})

        # Sort by index
        swings.sort(key=lambda x: x["index"])
        return swings
