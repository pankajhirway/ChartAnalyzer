"""Support and Resistance level detection."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from app.models.analysis import Level


@dataclass
class SRConfig:
    """Configuration for S/R detection."""
    lookback_period: int = 100
    min_touches: int = 2
    tolerance_pct: float = 1.0  # Price cluster tolerance
    pivot_lookback: int = 5  # Pivot point lookback
    volume_threshold: float = 1.5  # Volume spike threshold


class SupportResistanceDetector:
    """Detects support and resistance levels using multiple methods."""

    def __init__(self, config: Optional[SRConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or SRConfig()

    def detect_levels(self, df: pd.DataFrame) -> tuple[list[Level], list[Level]]:
        """Detect support and resistance levels.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        if df.empty or len(df) < self.config.pivot_lookback * 2:
            return [], []

        # Use lookback period
        lookback = min(self.config.lookback_period, len(df))
        data = df.tail(lookback).copy()

        # Detect using multiple methods
        pivot_levels = self._detect_pivot_levels(data)
        volume_levels = self._detect_volume_levels(data)
        ma_levels = self._detect_ma_levels(df)
        psychological_levels = self._detect_psychological_levels(df)

        # Combine and cluster levels
        all_levels = pivot_levels + volume_levels + ma_levels + psychological_levels
        clustered = self._cluster_levels(all_levels, df["close"].iloc[-1])

        # Separate into support and resistance
        current_price = float(df["close"].iloc[-1])
        support = [l for l in clustered if l.price < current_price and l.level_type == "support"]
        resistance = [l for l in clustered if l.price > current_price and l.level_type == "resistance"]

        # Sort by strength and proximity
        support.sort(key=lambda x: (-x.strength, abs(current_price - x.price)))
        resistance.sort(key=lambda x: (-x.strength, abs(current_price - x.price)))

        return support[:10], resistance[:10]  # Return top 10 of each

    def _detect_pivot_levels(self, df: pd.DataFrame) -> list[Level]:
        """Detect levels based on pivot points (swing highs/lows)."""
        levels = []
        lookback = self.config.pivot_lookback

        for i in range(lookback, len(df) - lookback):
            # Check for pivot high
            window_highs = df["high"].iloc[i - lookback:i + lookback + 1]
            if df["high"].iloc[i] == window_highs.max():
                levels.append(Level(
                    price=float(df["high"].iloc[i]),
                    strength=3,
                    touches=1,
                    level_type="resistance",
                    description="Pivot high resistance"
                ))

            # Check for pivot low
            window_lows = df["low"].iloc[i - lookback:i + lookback + 1]
            if df["low"].iloc[i] == window_lows.min():
                levels.append(Level(
                    price=float(df["low"].iloc[i]),
                    strength=3,
                    touches=1,
                    level_type="support",
                    description="Pivot low support"
                ))

        return levels

    def _detect_volume_levels(self, df: pd.DataFrame) -> list[Level]:
        """Detect levels based on volume profile."""
        levels = []

        if "volume" not in df.columns:
            return levels

        avg_volume = df["volume"].mean()
        volume_threshold = avg_volume * self.config.volume_threshold

        # Find high volume candles
        high_volume_mask = df["volume"] > volume_threshold
        high_volume_df = df[high_volume_mask]

        for idx, row in high_volume_df.iterrows():
            # High volume at highs = resistance
            if row["close"] > row["open"]:  # Bullish candle
                levels.append(Level(
                    price=float(row["high"]),
                    strength=4,
                    touches=1,
                    level_type="resistance",
                    description="High volume resistance"
                ))
            else:  # Bearish candle
                levels.append(Level(
                    price=float(row["low"]),
                    strength=4,
                    touches=1,
                    level_type="support",
                    description="High volume support"
                ))

        return levels

    def _detect_ma_levels(self, df: pd.DataFrame) -> list[Level]:
        """Detect levels based on key moving averages."""
        levels = []
        close = df["close"]

        ma_periods = [20, 50, 100, 200]

        for period in ma_periods:
            if len(close) >= period:
                ma_value = close.rolling(window=period).mean().iloc[-1]
                levels.append(Level(
                    price=float(ma_value),
                    strength=2,
                    touches=period,
                    level_type="support",  # Will be reassessed in clustering
                    description=f"SMA {period} dynamic support/resistance"
                ))

        return levels

    def _detect_psychological_levels(self, df: pd.DataFrame) -> list[Level]:
        """Detect psychological round number levels."""
        levels = []
        current_price = float(df["close"].iloc[-1])

        # Find relevant round numbers near current price
        # For Indian stocks, use 50, 100, 500, 1000 increments
        increments = [50, 100, 500, 1000]

        for inc in increments:
            lower = (current_price // inc) * inc
            upper = lower + inc

            # Add nearby levels
            for level_price in [lower, upper]:
                if 0.9 * current_price <= level_price <= 1.1 * current_price:
                    levels.append(Level(
                        price=float(level_price),
                        strength=2,
                        touches=0,
                        level_type="support" if level_price < current_price else "resistance",
                        description=f"Psychological level ({inc})"
                    ))

        return levels

    def _cluster_levels(self, levels: list[Level], current_price: float) -> list[Level]:
        """Cluster nearby levels and aggregate their strength."""
        if not levels:
            return []

        # Sort by price
        sorted_levels = sorted(levels, key=lambda x: x.price)
        tolerance = current_price * (self.config.tolerance_pct / 100)

        clustered = []
        current_cluster = [sorted_levels[0]]

        for level in sorted_levels[1:]:
            # Check if level is within tolerance of cluster
            if abs(level.price - current_cluster[0].price) <= tolerance:
                current_cluster.append(level)
            else:
                # Process current cluster
                clustered.append(self._merge_cluster(current_cluster, current_price))
                current_cluster = [level]

        # Don't forget the last cluster
        clustered.append(self._merge_cluster(current_cluster, current_price))

        return clustered

    def _merge_cluster(self, cluster: list[Level], current_price: float) -> Level:
        """Merge a cluster of levels into a single level."""
        if len(cluster) == 1:
            return cluster[0]

        # Weighted average price by strength
        total_strength = sum(l.strength for l in cluster)
        weighted_price = sum(l.price * l.strength for l in cluster) / total_strength

        # Aggregate touches and strength
        total_touches = sum(l.touches for l in cluster)
        avg_strength = min(5, total_strength // len(cluster) + 1)

        # Determine type based on price relative to current
        level_type = "support" if weighted_price < current_price else "resistance"

        return Level(
            price=weighted_price,
            strength=avg_strength,
            touches=total_touches,
            level_type=level_type,
            description=f"Clustered {level_type} ({len(cluster)} touches)"
        )

    def get_nearest_levels(
        self,
        df: pd.DataFrame,
        count: int = 3,
    ) -> tuple[list[Level], list[Level]]:
        """Get nearest support and resistance levels."""
        support, resistance = self.detect_levels(df)

        # Already sorted by proximity
        return support[:count], resistance[:count]
