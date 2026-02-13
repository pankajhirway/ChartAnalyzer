"""Stan Weinstein Stage Analysis Strategy."""

from typing import Optional

import numpy as np
import pandas as pd

from app.strategies.base import BaseStrategy, StrategyResult
from app.models.analysis import WeinsteinStage


class WeinsteinStrategy(BaseStrategy):
    """Stan Weinstein's Stage Analysis Strategy.

    Stage Classification:
    - Stage 1: Basing/Consolidation (Neutral)
    - Stage 2: Advancing (BULLISH - Buy Zone)
    - Stage 3: Topping/Distribution (Neutral/Caution)
    - Stage 4: Declining (BEARISH - Avoid/Short)

    Uses weekly charts for primary stage determination,
    daily charts for entry timing.
    """

    name = "Weinstein Stage Analysis"
    description = "Stan Weinstein's 4-stage market cycle analysis"

    # Weekly-equivalent periods (using daily data)
    WEEKLY_MA_PERIOD = 150  # ~30 weeks

    def analyze(self, df: pd.DataFrame, indicators: dict) -> StrategyResult:
        """Analyze stock using Stage Analysis.

        Scoring based on:
        - Current stage: 0-40 points
        - MA relationship: 0-25 points
        - Price action quality: 0-20 points
        - Volume confirmation: 0-15 points
        Total: 0-100 points
        """
        if df.empty or len(df) < 150:
            return StrategyResult(
                score=0,
                bullish_factors=[],
                bearish_factors=["Insufficient data"],
                warnings=["Need at least 150 bars for stage analysis"],
                signal="AVOID",
                conviction="LOW"
            )

        bullish_factors = []
        bearish_factors = []
        warnings = []

        # Determine current stage
        stage, stage_desc = self._determine_stage(df)
        stage_score = self._score_stage(stage, bullish_factors, bearish_factors, warnings)

        # Score MA relationship
        ma_score = self._score_ma_relationship(df, indicators, bullish_factors, bearish_factors)

        # Score price action
        price_score = self._score_price_action(df, indicators, bullish_factors, bearish_factors)

        # Score volume
        volume_score = self._score_volume(df, indicators, bullish_factors, bearish_factors)

        total_score = stage_score + ma_score + price_score + volume_score

        signal, conviction = self._get_signal_from_score(total_score)

        # Add stage to factors
        stage_info = f"Currently in {stage_desc}"
        if stage == WeinsteinStage.STAGE_2:
            bullish_factors.insert(0, stage_info)
        elif stage == WeinsteinStage.STAGE_4:
            bearish_factors.insert(0, stage_info)
        else:
            warnings.append(stage_info)

        return StrategyResult(
            score=total_score,
            bullish_factors=bullish_factors,
            bearish_factors=bearish_factors,
            warnings=warnings,
            signal=signal,
            conviction=conviction
        )

    def _determine_stage(self, df: pd.DataFrame) -> tuple[WeinsteinStage, str]:
        """Determine the current Weinstein stage.

        Returns:
            Tuple of (stage enum, description string)
        """
        close = df["close"]
        current_price = float(close.iloc[-1])

        # Calculate 30-week MA equivalent
        weekly_ma = close.rolling(window=self.WEEKLY_MA_PERIOD).mean()
        current_ma = float(weekly_ma.iloc[-1])

        # Calculate MA slope
        ma_slope = self._calculate_slope(weekly_ma, 50)

        # Price position relative to MA
        price_above_ma = current_price > current_ma

        # Check for trend patterns
        lookback = min(100, len(df) - 1)
        higher_highs = self._check_higher_highs(df, lookback)
        lower_lows = self._check_lower_lows(df, lookback)

        # Stage determination logic
        if ma_slope > 0.02 and price_above_ma:
            # Rising MA with price above = Stage 2
            if higher_highs:
                return WeinsteinStage.STAGE_2, "Stage 2: Advancing - Strong uptrend"
            else:
                return WeinsteinStage.STAGE_2, "Stage 2: Advancing - Consolidating in uptrend"

        elif ma_slope < -0.02 and not price_above_ma:
            # Falling MA with price below = Stage 4
            if lower_lows:
                return WeinsteinStage.STAGE_4, "Stage 4: Declining - Strong downtrend"
            else:
                return WeinsteinStage.STAGE_4, "Stage 4: Declining - Consolidating in downtrend"

        elif abs(ma_slope) <= 0.02:
            # Flat MA = Stage 1 or 3
            # Check where price came from
            prior_price = float(close.iloc[-lookback]) if len(close) > lookback else current_price
            prior_ma = float(weekly_ma.iloc[-lookback]) if len(weekly_ma) > lookback else current_ma

            # Prior downtrend leading to flat = Stage 1 (Basing)
            # Prior uptrend leading to flat = Stage 3 (Topping)
            prior_trend = "down" if prior_price < prior_ma else "up"

            if prior_trend == "down":
                return WeinsteinStage.STAGE_1, "Stage 1: Basing - Watch for breakout"
            else:
                return WeinsteinStage.STAGE_3, "Stage 3: Topping - Consider reducing position"

        else:
            # Transitional state
            if price_above_ma:
                return WeinsteinStage.STAGE_1, "Transitional - Potential Stage 2 breakout"
            else:
                return WeinsteinStage.STAGE_3, "Transitional - Potential Stage 4 breakdown"

    def _score_stage(
        self,
        stage: WeinsteinStage,
        bullish: list,
        bearish: list,
        warnings: list,
    ) -> float:
        """Score based on current stage (0-40 points)."""
        scores = {
            WeinsteinStage.STAGE_2: 40,  # Buy zone
            WeinsteinStage.STAGE_1: 25,  # Basing - neutral
            WeinsteinStage.STAGE_3: 15,  # Topping - caution
            WeinsteinStage.STAGE_4: 0,   # Declining - avoid
        }

        score = scores.get(stage, 0)

        if stage == WeinsteinStage.STAGE_2:
            bullish.append("Stock in Stage 2 advancing phase")
        elif stage == WeinsteinStage.STAGE_4:
            bearish.append("Stock in Stage 4 declining phase")
        elif stage == WeinsteinStage.STAGE_1:
            warnings.append("Stock in Stage 1 basing - wait for breakout")
        else:
            warnings.append("Stock in Stage 3 topping - caution advised")

        return score

    def _score_ma_relationship(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        bearish: list,
    ) -> float:
        """Score MA relationship (0-25 points)."""
        score = 0.0
        close = df["close"]
        current_price = float(close.iloc[-1])

        # Get MAs
        sma_50 = self._safe_get(indicators, "sma_50")
        sma_150 = self._safe_get(indicators, "sma_150")
        sma_200 = self._safe_get(indicators, "sma_200")

        # Price above 30-week MA (150-day)
        if sma_150:
            if current_price > sma_150:
                score += 10
                bullish.append("Price above 30-week MA")
            else:
                bearish.append("Price below 30-week MA")

        # MA slope (30-week)
        if len(close) >= 150:
            weekly_ma = close.rolling(window=150).mean()
            slope = self._calculate_slope(weekly_ma, 20)

            if slope > 0.02:
                score += 10
                bullish.append("30-week MA trending up strongly")
            elif slope > 0:
                score += 7
                bullish.append("30-week MA trending up")
            elif slope < -0.02:
                bearish.append("30-week MA trending down strongly")
            else:
                score += 3
                # Flat MA - could be basing or topping

        # Price distance from MA (not too extended)
        if sma_150 and current_price > sma_150:
            distance = (current_price - sma_150) / sma_150 * 100
            if distance < 30:
                score += 5
            elif distance > 50:
                # Too extended
                score -= 3

        return max(0, min(25, score))

    def _score_price_action(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        bearish: list,
    ) -> float:
        """Score price action quality (0-20 points)."""
        score = 0.0

        if len(df) < 50:
            return 0

        close = df["close"]
        high = df["high"]
        low = df["low"]

        # Higher highs and higher lows
        lookback = 30
        if self._check_higher_highs(df, lookback) and self._check_higher_lows(df, lookback):
            score += 10
            bullish.append("Making higher highs and higher lows")
        elif self._check_lower_lows(df, lookback) and self._check_lower_highs(df, lookback):
            bearish.append("Making lower lows and lower highs")
        else:
            score += 3

        # Check for breakouts
        recent_high = high.iloc[-20:].max()
        if close.iloc[-1] >= recent_high * 0.98:
            score += 5
            bullish.append("Near recent highs")

        # Check for support at MA
        sma_50 = self._safe_get(indicators, "sma_50")
        if sma_50:
            recent_low = low.iloc[-10:].min()
            if abs(recent_low - sma_50) / sma_50 < 0.02:
                score += 5
                bullish.append("Found support at 50-day MA")

        return min(20, score)

    def _score_volume(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        bearish: list,
    ) -> float:
        """Score volume characteristics (0-15 points)."""
        score = 0.0

        if "volume" not in df.columns:
            return 0

        volume = df["volume"]

        # Volume trend
        if len(volume) >= 50:
            vol_sma_20 = volume.rolling(window=20).mean()
            vol_sma_50 = volume.rolling(window=50).mean()

            if vol_sma_20.iloc[-1] > vol_sma_50.iloc[-1]:
                score += 7
                bullish.append("Volume trend increasing")
            else:
                score += 2

        # Volume on up days vs down days
        recent = df.tail(20)
        up_days = recent[recent["close"] > recent["open"]]
        down_days = recent[recent["close"] < recent["open"]]

        if len(up_days) > 0 and len(down_days) > 0:
            up_vol_avg = up_days["volume"].mean()
            down_vol_avg = down_days["volume"].mean()

            if up_vol_avg > down_vol_avg * 1.2:
                score += 8
                bullish.append("Higher volume on up days")
            elif down_vol_avg > up_vol_avg * 1.2:
                bearish.append("Higher volume on down days")
            else:
                score += 4

        return min(15, score)

    def _calculate_slope(self, series: pd.Series, lookback: int) -> float:
        """Calculate slope of a series over lookback period."""
        if len(series) < lookback:
            return 0.0

        recent = series.tail(lookback).dropna()
        if len(recent) < 2:
            return 0.0

        start = recent.iloc[0]
        end = recent.iloc[-1]

        if start == 0:
            return 0.0

        return float((end - start) / start)

    def _check_higher_highs(self, df: pd.DataFrame, lookback: int) -> bool:
        """Check for higher highs pattern."""
        if len(df) < lookback:
            return False

        highs = df["high"].tail(lookback).values
        peaks = []

        for i in range(1, len(highs) - 1):
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                peaks.append(highs[i])

        if len(peaks) < 2:
            return False

        # Check if peaks are ascending
        return all(peaks[i] < peaks[i + 1] for i in range(len(peaks) - 1))

    def _check_higher_lows(self, df: pd.DataFrame, lookback: int) -> bool:
        """Check for higher lows pattern."""
        if len(df) < lookback:
            return False

        lows = df["low"].tail(lookback).values
        troughs = []

        for i in range(1, len(lows) - 1):
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                troughs.append(lows[i])

        if len(troughs) < 2:
            return False

        return all(troughs[i] < troughs[i + 1] for i in range(len(troughs) - 1))

    def _check_lower_lows(self, df: pd.DataFrame, lookback: int) -> bool:
        """Check for lower lows pattern."""
        if len(df) < lookback:
            return False

        lows = df["low"].tail(lookback).values
        troughs = []

        for i in range(1, len(lows) - 1):
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                troughs.append(lows[i])

        if len(troughs) < 2:
            return False

        return all(troughs[i] > troughs[i + 1] for i in range(len(troughs) - 1))

    def _check_lower_highs(self, df: pd.DataFrame, lookback: int) -> bool:
        """Check for lower highs pattern."""
        if len(df) < lookback:
            return False

        highs = df["high"].tail(lookback).values
        peaks = []

        for i in range(1, len(highs) - 1):
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                peaks.append(highs[i])

        if len(peaks) < 2:
            return False

        return all(peaks[i] > peaks[i + 1] for i in range(len(peaks) - 1))

    def get_stage(self, df: pd.DataFrame) -> WeinsteinStage:
        """Get current stage (public method)."""
        stage, _ = self._determine_stage(df)
        return stage
