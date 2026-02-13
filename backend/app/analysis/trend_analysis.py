"""Trend analysis module."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from app.models.analysis import TrendType, WeinsteinStage


@dataclass
class TrendConfig:
    """Configuration for trend analysis."""
    short_ma_period: int = 20
    medium_ma_period: int = 50
    long_ma_period: int = 200
    weekly_ma_period: int = 30  # For Weinstein stage analysis
    trend_strength_threshold: float = 25.0  # ADX threshold


class TrendAnalyzer:
    """Analyzes market trends using multiple methods."""

    def __init__(self, config: Optional[TrendConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or TrendConfig()

    def analyze_trend(self, df: pd.DataFrame) -> tuple[TrendType, float, str]:
        """Analyze the current trend.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Tuple of (trend_type, trend_strength, trend_notes)
        """
        if df.empty or len(df) < 50:
            return TrendType.NEUTRAL, 0.0, "Insufficient data"

        close = df["close"]
        current_price = float(close.iloc[-1])

        # Calculate moving averages
        sma_20 = close.rolling(window=self.config.short_ma_period).mean()
        sma_50 = close.rolling(window=self.config.medium_ma_period).mean()
        sma_200 = close.rolling(window=self.config.long_ma_period).mean() if len(close) >= 200 else None

        # Calculate slopes
        slope_20 = self._calculate_slope(sma_20, 10)
        slope_50 = self._calculate_slope(sma_50, 20)

        # Calculate higher highs / higher lows
        hh_hl = self._check_higher_highs_lows(df)
        ll_lh = self._check_lower_lows_highs(df)

        # Calculate trend strength using price action
        strength_score = 0.0
        notes = []

        # Price relative to MAs
        current_sma_20 = float(sma_20.iloc[-1])
        current_sma_50 = float(sma_50.iloc[-1])

        if current_price > current_sma_20:
            strength_score += 15
            notes.append("Price above SMA20")
        else:
            strength_score -= 10

        if current_price > current_sma_50:
            strength_score += 15
            notes.append("Price above SMA50")
        else:
            strength_score -= 15

        # MA alignment
        if current_sma_20 > current_sma_50:
            strength_score += 15
            notes.append("Bullish MA alignment")
        else:
            strength_score -= 10

        # MA slopes
        if slope_20 > 0:
            strength_score += 10
        else:
            strength_score -= 10

        if slope_50 > 0:
            strength_score += 10
        else:
            strength_score -= 10

        # Higher highs/lows pattern
        if hh_hl:
            strength_score += 20
            notes.append("Higher highs and higher lows")
        elif ll_lh:
            strength_score -= 20
            notes.append("Lower highs and lower lows")

        # SMA200 check
        if sma_200 is not None:
            current_sma_200 = float(sma_200.iloc[-1])
            if current_price > current_sma_200:
                strength_score += 15
                notes.append("Price above SMA200")
            else:
                strength_score -= 10

        # Normalize strength to 0-100
        strength_score = max(0, min(100, 50 + strength_score))

        # Determine trend type
        if strength_score >= 65:
            trend = TrendType.BULLISH
        elif strength_score <= 35:
            trend = TrendType.BEARISH
        else:
            trend = TrendType.NEUTRAL

        return trend, strength_score, "; ".join(notes) if notes else "Mixed signals"

    def determine_weinstein_stage(self, df: pd.DataFrame) -> tuple[WeinsteinStage, str]:
        """Determine Weinstein stage (1-4).

        Uses weekly-equivalent analysis for stage determination.

        Args:
            df: DataFrame with OHLCV data (daily)

        Returns:
            Tuple of (stage, description)
        """
        if df.empty or len(df) < 200:
            return WeinsteinStage.STAGE_1, "Insufficient data for stage analysis"

        close = df["close"]
        current_price = float(close.iloc[-1])

        # Calculate weekly-equivalent MA (30-week MA ~ 150-day MA)
        weekly_ma = close.rolling(window=150).mean()
        current_weekly_ma = float(weekly_ma.iloc[-1]) if not weekly_ma.empty else current_price

        # Calculate MA slope (30-week lookback ~ 150 days)
        ma_slope = self._calculate_slope(weekly_ma, 150)

        # Check price position relative to MA
        price_above_ma = current_price > current_weekly_ma

        # Check price action pattern
        lookback = min(100, len(df) - 1)
        recent_highs = df["high"].tail(lookback)
        recent_lows = df["low"].tail(lookback)

        higher_highs = self._count_higher_highs(recent_highs, 20)
        lower_lows = self._count_lower_lows(recent_lows, 20)

        # Stage determination logic
        if price_above_ma and ma_slope > 0.01:
            # Price above rising MA
            if higher_highs > lower_lows:
                return WeinsteinStage.STAGE_2, "Stage 2: Advancing - BUY ZONE"
            else:
                # Could be transitioning
                return WeinsteinStage.STAGE_2, "Stage 2: Advancing (consolidating)"

        elif not price_above_ma and ma_slope < -0.01:
            # Price below falling MA
            if lower_lows > higher_highs:
                return WeinsteinStage.STAGE_4, "Stage 4: Declining - AVOID/SHORT"
            else:
                return WeinsteinStage.STAGE_4, "Stage 4: Declining (potential bottom)"

        elif abs(ma_slope) <= 0.01:
            # MA is flat - basing or topping
            # Check price position for the past period
            avg_price = close.tail(lookback).mean()

            # Check if we came from uptrend or downtrend
            prior_ma = weekly_ma.iloc[-lookback] if len(weekly_ma) > lookback else current_weekly_ma
            prior_price = close.iloc[-lookback] if len(close) > lookback else current_price

            if prior_price < prior_ma and price_above_ma:
                # Coming from below - Stage 1 (Basing)
                return WeinsteinStage.STAGE_1, "Stage 1: Basing - Watch for breakout"
            elif prior_price > prior_ma and not price_above_ma:
                # Coming from above - Stage 3 (Topping)
                return WeinsteinStage.STAGE_3, "Stage 3: Topping - Consider selling"
            else:
                # Ambiguous - check volume
                return WeinsteinStage.STAGE_1, "Stage 1/3: Consolidating - Wait for direction"

        else:
            # Default to neutral
            return WeinsteinStage.STAGE_1, "Transitional - Monitor for direction"

    def _calculate_slope(self, series: pd.Series, lookback: int) -> float:
        """Calculate slope of a series."""
        if len(series) < lookback:
            return 0.0

        recent = series.tail(lookback).dropna()
        if len(recent) < 2:
            return 0.0

        # Percentage change over period
        start_val = recent.iloc[0]
        end_val = recent.iloc[-1]

        if start_val == 0:
            return 0.0

        return (end_val - start_val) / start_val

    def _check_higher_highs_lows(self, df: pd.DataFrame, lookback: int = 20) -> bool:
        """Check if price is making higher highs and higher lows."""
        if len(df) < lookback:
            return False

        recent = df.tail(lookback)
        highs = recent["high"].values
        lows = recent["low"].values

        # Check for higher highs
        hh_count = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i - 1])

        # Check for higher lows
        hl_count = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i - 1])

        # At least 60% should be higher
        return hh_count > len(highs) * 0.6 and hl_count > len(lows) * 0.6

    def _check_lower_lows_highs(self, df: pd.DataFrame, lookback: int = 20) -> bool:
        """Check if price is making lower lows and lower highs."""
        if len(df) < lookback:
            return False

        recent = df.tail(lookback)
        highs = recent["high"].values
        lows = recent["low"].values

        # Check for lower highs
        lh_count = sum(1 for i in range(1, len(highs)) if highs[i] < highs[i - 1])

        # Check for lower lows
        ll_count = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i - 1])

        return lh_count > len(highs) * 0.6 and ll_count > len(lows) * 0.6

    def _count_higher_highs(self, highs: pd.Series, lookback: int) -> int:
        """Count number of higher highs."""
        if len(highs) < lookback:
            return 0

        count = 0
        prev_high = highs.iloc[0]

        for i in range(1, len(highs)):
            if highs.iloc[i] > prev_high:
                count += 1
            prev_high = highs.iloc[i]

        return count

    def _count_lower_lows(self, lows: pd.Series, lookback: int) -> int:
        """Count number of lower lows."""
        if len(lows) < lookback:
            return 0

        count = 0
        prev_low = lows.iloc[0]

        for i in range(1, len(lows)):
            if lows.iloc[i] < prev_low:
                count += 1
            prev_low = lows.iloc[i]

        return count

    def is_uptrend(self, df: pd.DataFrame) -> bool:
        """Quick check if stock is in uptrend."""
        trend, _, _ = self.analyze_trend(df)
        return trend == TrendType.BULLISH

    def is_downtrend(self, df: pd.DataFrame) -> bool:
        """Quick check if stock is in downtrend."""
        trend, _, _ = self.analyze_trend(df)
        return trend == TrendType.BEARISH
