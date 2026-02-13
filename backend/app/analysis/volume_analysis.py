"""Volume analysis module."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class VolumeConfig:
    """Configuration for volume analysis."""
    sma_periods: list[int] = None
    spike_threshold: float = 1.5  # 150% of average
    accumulation_threshold: float = 2.0  # For detecting accumulation

    def __post_init__(self):
        if self.sma_periods is None:
            self.sma_periods = [20, 50]


class VolumeAnalyzer:
    """Analyzes volume patterns and characteristics."""

    def __init__(self, config: Optional[VolumeConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or VolumeConfig()

    def analyze_volume(self, df: pd.DataFrame) -> dict:
        """Perform comprehensive volume analysis.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary with volume analysis results
        """
        if df.empty or "volume" not in df.columns:
            return self._empty_result()

        volume = df["volume"]
        close = df["close"]

        result = {
            "current_volume": int(volume.iloc[-1]),
            "avg_volume_20": None,
            "avg_volume_50": None,
            "volume_ratio": None,
            "volume_trend": "neutral",
            "on_breakout": False,
            "accumulation_detected": False,
            "distribution_detected": False,
            "volume_confirmation": False,
            "notes": [],
        }

        # Calculate average volumes
        if len(volume) >= 20:
            result["avg_volume_20"] = float(volume.rolling(window=20).mean().iloc[-1])

        if len(volume) >= 50:
            result["avg_volume_50"] = float(volume.rolling(window=50).mean().iloc[-1])

        # Calculate volume ratio
        if result["avg_volume_20"]:
            result["volume_ratio"] = result["current_volume"] / result["avg_volume_20"]

        # Volume trend
        result["volume_trend"] = self._analyze_volume_trend(volume)

        # Breakout detection
        result["on_breakout"] = self._detect_breakout_volume(df)

        # Accumulation/Distribution
        acc_dist = self._detect_accumulation_distribution(df)
        result["accumulation_detected"] = acc_dist["accumulation"]
        result["distribution_detected"] = acc_dist["distribution"]

        # Volume confirmation for price move
        result["volume_confirmation"] = self._check_volume_confirmation(df)

        # Generate notes
        result["notes"] = self._generate_notes(result, df)

        return result

    def _empty_result(self) -> dict:
        """Return empty result structure."""
        return {
            "current_volume": 0,
            "avg_volume_20": None,
            "avg_volume_50": None,
            "volume_ratio": None,
            "volume_trend": "neutral",
            "on_breakout": False,
            "accumulation_detected": False,
            "distribution_detected": False,
            "volume_confirmation": False,
            "notes": [],
        }

    def _analyze_volume_trend(self, volume: pd.Series) -> str:
        """Analyze if volume is trending up or down."""
        if len(volume) < 50:
            return "neutral"

        avg_20 = volume.rolling(window=20).mean()
        avg_50 = volume.rolling(window=50).mean()

        if avg_20.empty or avg_50.empty:
            return "neutral"

        current_20 = avg_20.iloc[-1]
        current_50 = avg_50.iloc[-1]

        if current_20 > current_50 * 1.2:
            return "increasing"
        elif current_20 < current_50 * 0.8:
            return "decreasing"
        else:
            return "stable"

    def _detect_breakout_volume(self, df: pd.DataFrame) -> bool:
        """Detect if current volume is breakout-level."""
        if len(df) < 20:
            return False

        volume = df["volume"]
        close = df["close"]

        avg_volume = volume.rolling(window=20).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        current_close = close.iloc[-1]
        prev_close = close.iloc[-2] if len(close) > 1 else current_close

        # Breakout volume: high volume on price move
        price_change_pct = abs((current_close - prev_close) / prev_close) * 100

        return (
            current_volume > avg_volume * self.config.spike_threshold
            and price_change_pct > 1.0
        )

    def _detect_accumulation_distribution(self, df: pd.DataFrame) -> dict:
        """Detect accumulation or distribution patterns."""
        result = {"accumulation": False, "distribution": False}

        if len(df) < 20:
            return result

        volume = df["volume"]
        close = df["close"]

        # Look at recent price action
        recent_df = df.tail(20)
        avg_volume = volume.rolling(window=20).mean().iloc[-1]

        # Accumulation: High volume on up days, low volume on down days
        up_days = recent_df[recent_df["close"] > recent_df["open"]]
        down_days = recent_df[recent_df["close"] < recent_df["open"]]

        if len(up_days) > 0 and len(down_days) > 0:
            avg_up_volume = up_days["volume"].mean()
            avg_down_volume = down_days["volume"].mean()

            if avg_up_volume > avg_down_volume * self.config.accumulation_threshold:
                result["accumulation"] = True

            if avg_down_volume > avg_up_volume * self.config.accumulation_threshold:
                result["distribution"] = True

        return result

    def _check_volume_confirmation(self, df: pd.DataFrame) -> bool:
        """Check if volume confirms recent price move."""
        if len(df) < 10:
            return False

        recent = df.tail(10)
        close = recent["close"]
        volume = recent["volume"]

        # Check if price trend is confirmed by volume
        price_trend = 1 if close.iloc[-1] > close.iloc[0] else -1

        # Volume should be higher on trend direction days
        if price_trend > 0:
            up_days = recent[recent["close"] > recent["open"]]
            down_days = recent[recent["close"] < recent["open"]]

            if len(up_days) > 0 and len(down_days) > 0:
                avg_up_vol = up_days["volume"].mean()
                avg_down_vol = down_days["volume"].mean()
                return avg_up_vol > avg_down_vol

        return False

    def _generate_notes(self, result: dict, df: pd.DataFrame) -> list[str]:
        """Generate human-readable notes about volume."""
        notes = []

        if result["volume_ratio"] and result["volume_ratio"] > 1.5:
            notes.append(f"Volume {result['volume_ratio']:.1f}x above average")

        if result["on_breakout"]:
            notes.append("Breakout volume detected")

        if result["accumulation_detected"]:
            notes.append("Accumulation pattern: high volume on up days")

        if result["distribution_detected"]:
            notes.append("Distribution pattern: high volume on down days")

        if result["volume_trend"] == "increasing":
            notes.append("Volume trend increasing")
        elif result["volume_trend"] == "decreasing":
            notes.append("Volume trend decreasing")

        return notes

    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume."""
        if df.empty or "volume" not in df.columns:
            return pd.Series()

        close = df["close"]
        volume = df["volume"]

        direction = np.sign(close.diff()).fillna(0)
        obv = (volume * direction).cumsum()

        return obv

    def is_volume_drying_up(self, df: pd.DataFrame, lookback: int = 10) -> bool:
        """Check if volume is drying up (contracting).

        This is important for VCP detection.
        """
        if len(df) < lookback:
            return False

        volume = df["volume"].tail(lookback)
        avg_volume = df["volume"].rolling(window=50).mean().iloc[-1]

        # Volume should be decreasing and below average
        recent_avg = volume.mean()
        is_decreasing = volume.iloc[-1] < volume.iloc[0]
        is_below_avg = recent_avg < avg_volume * 0.7

        return is_decreasing and is_below_avg

    def get_volume_climax(self, df: pd.DataFrame) -> Optional[dict]:
        """Detect volume climax (exhaustion)."""
        if len(df) < 20:
            return None

        volume = df["volume"]
        close = df["close"]

        avg_volume = volume.rolling(window=20).mean().iloc[-1]
        current_volume = volume.iloc[-1]

        # Volume climax: extremely high volume
        if current_volume > avg_volume * 3.0:
            price_change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100

            return {
                "detected": True,
                "volume_ratio": current_volume / avg_volume,
                "price_change_pct": price_change,
                "type": "buying_climax" if price_change > 0 else "selling_climax",
            }

        return {"detected": False}
