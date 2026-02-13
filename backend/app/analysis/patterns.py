"""Chart pattern detection module."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from app.models.analysis import PatternType, PatternMatch


@dataclass
class PatternConfig:
    """Configuration for pattern detection."""
    min_pattern_bars: int = 20
    max_pattern_bars: int = 100
    tolerance: float = 0.03  # 3% tolerance for level matching


class PatternDetector:
    """Detects chart patterns in price data."""

    def __init__(self, config: Optional[PatternConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or PatternConfig()

    def detect_patterns(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect all chart patterns.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            List of detected patterns
        """
        if df.empty or len(df) < self.config.min_pattern_bars:
            return []

        patterns = []

        # Detect each pattern type
        patterns.extend(self._detect_cup_handle(df))
        patterns.extend(self._detect_vcp(df))
        patterns.extend(self._detect_double_top_bottom(df))
        patterns.extend(self._detect_head_shoulders(df))
        patterns.extend(self._detect_triangles(df))
        patterns.extend(self._detect_flags(df))
        patterns.extend(self._detect_wedges(df))
        patterns.extend(self._detect_base_breakout(df))
        patterns.extend(self._detect_high_tight_flag(df))
        patterns.extend(self._detect_ma_pullback(df))

        # Sort by confidence
        patterns.sort(key=lambda x: x.confidence, reverse=True)

        return patterns

    def _detect_cup_handle(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect Cup and Handle pattern."""
        patterns = []

        if len(df) < 60:
            return patterns

        # Look at recent data
        lookback = min(100, len(df))
        data = df.tail(lookback)

        high = data["high"]
        low = data["low"]
        close = data["close"]

        # Find the left side high (cup rim)
        left_high_idx = high.iloc[:len(high) // 2].idxmax()
        left_high = high.loc[left_high_idx]

        # Find the cup bottom
        bottom_idx = low.idxmin()
        bottom = low.loc[bottom_idx]

        # Find right side (current area)
        right_high = high.iloc[-20:].max()

        # Cup criteria
        cup_depth = (left_high - bottom) / left_high

        if 0.10 < cup_depth < 0.35:  # Cup should be 10-35% deep
            # Check if right side is forming
            handle_area = close.iloc[-10:]
            handle_high = handle_area.max()
            handle_low = handle_area.min()

            # Handle should be shallow pullback
            handle_depth = (handle_high - handle_low) / handle_high

            if handle_depth < 0.15 and handle_low > bottom:
                breakout_level = max(left_high, right_high)

                patterns.append(PatternMatch(
                    pattern_type=PatternType.CUP_HANDLE,
                    pattern_name="Cup and Handle",
                    bullish=True,
                    completion_pct=min(100, 90 + (right_high / left_high) * 10),
                    breakout_level=float(breakout_level),
                    target_price=float(breakout_level * 1.2),
                    stop_loss=float(handle_low * 0.98),
                    confidence=0.75,
                    description=f"Cup depth {cup_depth * 100:.1f}%, handle depth {handle_depth * 100:.1f}%"
                ))

        return patterns

    def _detect_vcp(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect Volatility Contraction Pattern (Minervini)."""
        patterns = []

        if len(df) < 80:
            return patterns

        # Look for contraction phases
        lookback = min(150, len(df))
        data = df.tail(lookback)

        high = data["high"]
        low = data["low"]
        close = data["close"]

        # Find pivot points
        pivots = self._find_pivots(data)

        if len(pivots) < 3:
            return patterns

        # Analyze contractions
        contractions = []
        for i in range(len(pivots) - 1):
            pivot_high = pivots[i]["high"]
            pivot_low = pivots[i + 1]["low"]
            contraction = (pivot_high - pivot_low) / pivot_high
            contractions.append(contraction)

        # VCP: contractions should be getting smaller
        if len(contractions) >= 2:
            is_contracting = all(
                contractions[i] > contractions[i + 1]
                for i in range(len(contractions) - 1)
            )

            if is_contracting:
                current_price = float(close.iloc[-1])
                recent_high = float(high.iloc[-20:].max())

                # Volume should be drying up
                volume = data["volume"]
                recent_vol = volume.iloc[-10:].mean()
                earlier_vol = volume.iloc[-50:-10].mean()
                vol_drying = recent_vol < earlier_vol * 0.8

                confidence = 0.7 if vol_drying else 0.55

                patterns.append(PatternMatch(
                    pattern_type=PatternType.VCP,
                    pattern_name="Volatility Contraction Pattern",
                    bullish=True,
                    completion_pct=80 if vol_drying else 60,
                    breakout_level=float(recent_high),
                    target_price=float(recent_high * 1.15),
                    stop_loss=float(pivots[-1]["low"] * 0.97),
                    confidence=confidence,
                    description=f"{len(contractions)} contractions, {'volume drying' if vol_drying else 'volume not confirmed'}"
                ))

        return patterns

    def _detect_double_top_bottom(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect Double Top and Double Bottom patterns."""
        patterns = []

        if len(df) < 40:
            return patterns

        lookback = min(80, len(df))
        data = df.tail(lookback)

        high = data["high"]
        low = data["low"]
        close = data["close"]
        current_price = float(close.iloc[-1])

        # Find peaks and troughs
        peaks = self._find_peaks(high, 5)
        troughs = self._find_troughs(low, 5)

        # Double Top: Two peaks at similar levels
        if len(peaks) >= 2:
            peak1 = float(high.iloc[peaks[-2]])
            peak2 = float(high.iloc[peaks[-1]])
            neckline = float(low.iloc[peaks[-1]:].min())

            if abs(peak1 - peak2) / peak1 < 0.03:  # Peaks within 3%
                patterns.append(PatternMatch(
                    pattern_type=PatternType.DOUBLE_TOP,
                    pattern_name="Double Top",
                    bullish=False,
                    completion_pct=70 if current_price < (peak1 + neckline) / 2 else 50,
                    breakout_level=float(neckline),
                    target_price=float(neckline - (peak1 - neckline)),
                    stop_loss=float(peak2 * 1.02),
                    confidence=0.65,
                    description=f"Two peaks at {peak1:.2f} and {peak2:.2f}"
                ))

        # Double Bottom: Two troughs at similar levels
        if len(troughs) >= 2:
            trough1 = float(low.iloc[troughs[-2]])
            trough2 = float(low.iloc[troughs[-1]])
            neckline = float(high.iloc[troughs[-1]:].max())

            if abs(trough1 - trough2) / trough1 < 0.03:
                patterns.append(PatternMatch(
                    pattern_type=PatternType.DOUBLE_BOTTOM,
                    pattern_name="Double Bottom",
                    bullish=True,
                    completion_pct=70 if current_price > (trough1 + neckline) / 2 else 50,
                    breakout_level=float(neckline),
                    target_price=float(neckline + (neckline - trough1)),
                    stop_loss=float(trough2 * 0.98),
                    confidence=0.65,
                    description=f"Two troughs at {trough1:.2f} and {trough2:.2f}"
                ))

        return patterns

    def _detect_head_shoulders(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect Head and Shoulders patterns."""
        patterns = []

        if len(df) < 60:
            return patterns

        lookback = min(100, len(df))
        data = df.tail(lookback)

        high = data["high"]
        low = data["low"]
        close = data["close"]

        peaks = self._find_peaks(high, 10)

        if len(peaks) >= 3:
            left_shoulder = float(high.iloc[peaks[-3]])
            head = float(high.iloc[peaks[-2]])
            right_shoulder = float(high.iloc[peaks[-1]])

            # Head should be higher than shoulders
            if head > left_shoulder and head > right_shoulder:
                # Shoulders should be roughly equal
                if abs(left_shoulder - right_shoulder) / left_shoulder < 0.05:
                    neckline = float(low.iloc[peaks[-3]:peaks[-1]].min())

                    # Regular H&S (bearish)
                    patterns.append(PatternMatch(
                        pattern_type=PatternType.HEAD_SHOULDERS,
                        pattern_name="Head and Shoulders",
                        bullish=False,
                        completion_pct=75,
                        breakout_level=float(neckline),
                        target_price=float(neckline - (head - neckline)),
                        stop_loss=float(head * 1.02),
                        confidence=0.70,
                        description=f"Head at {head:.2f}, shoulders at {left_shoulder:.2f}/{right_shoulder:.2f}"
                    ))

        # Inverse H&S (bullish) - look at lows
        troughs = self._find_troughs(low, 10)

        if len(troughs) >= 3:
            left_shoulder = float(low.iloc[troughs[-3]])
            head = float(low.iloc[troughs[-2]])
            right_shoulder = float(low.iloc[troughs[-1]])

            if head < left_shoulder and head < right_shoulder:
                if abs(left_shoulder - right_shoulder) / left_shoulder < 0.05:
                    neckline = float(high.iloc[troughs[-3]:troughs[-1]].max())

                    patterns.append(PatternMatch(
                        pattern_type=PatternType.HEAD_SHOULDERS_INVERSE,
                        pattern_name="Inverse Head and Shoulders",
                        bullish=True,
                        completion_pct=75,
                        breakout_level=float(neckline),
                        target_price=float(neckline + (neckline - head)),
                        stop_loss=float(head * 0.98),
                        confidence=0.70,
                        description=f"Head at {head:.2f}, shoulders at {left_shoulder:.2f}/{right_shoulder:.2f}"
                    ))

        return patterns

    def _detect_triangles(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect ascending and descending triangles."""
        patterns = []

        if len(df) < 30:
            return patterns

        lookback = min(50, len(df))
        data = df.tail(lookback)

        high = data["high"]
        low = data["low"]
        close = data["close"]

        # Calculate trendlines
        highs_trend = np.polyfit(range(len(high)), high.values, 1)
        lows_trend = np.polyfit(range(len(low)), low.values, 1)

        high_slope = highs_trend[0]
        low_slope = lows_trend[0]

        current_price = float(close.iloc[-1])

        # Ascending Triangle: flat top, rising bottom
        if abs(high_slope) < 0.1 and low_slope > 0.2:
            resistance = float(high.max())
            patterns.append(PatternMatch(
                pattern_type=PatternType.ASCENDING_TRIANGLE,
                pattern_name="Ascending Triangle",
                bullish=True,
                completion_pct=80 if current_price > resistance * 0.98 else 60,
                breakout_level=float(resistance),
                target_price=float(resistance * 1.1),
                stop_loss=float(low.iloc[-1] * 0.97),
                confidence=0.70,
                description="Flat resistance with rising support"
            ))

        # Descending Triangle: falling top, flat bottom
        if high_slope < -0.2 and abs(low_slope) < 0.1:
            support = float(low.min())
            patterns.append(PatternMatch(
                pattern_type=PatternType.DESCENDING_TRIANGLE,
                pattern_name="Descending Triangle",
                bullish=False,
                completion_pct=80 if current_price < support * 1.02 else 60,
                breakout_level=float(support),
                target_price=float(support * 0.9),
                stop_loss=float(high.iloc[-1] * 1.03),
                confidence=0.70,
                description="Falling resistance with flat support"
            ))

        return patterns

    def _detect_flags(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect Flag and Pennant patterns."""
        patterns = []

        if len(df) < 30:
            return patterns

        # Look for sharp move followed by consolidation
        lookback = min(40, len(df))
        data = df.tail(lookback)

        close = data["close"]
        high = data["high"]
        low = data["low"]

        # Sharp move in first 10 bars
        first_move = (close.iloc[10] - close.iloc[0]) / close.iloc[0] * 100

        # Consolidation in remaining bars
        consolidation = close.iloc[10:]
        range_pct = (consolidation.max() - consolidation.min()) / consolidation.mean() * 100

        if abs(first_move) > 10 and range_pct < 8:
            is_bullish = first_move > 0
            current_price = float(close.iloc[-1])

            if is_bullish:
                patterns.append(PatternMatch(
                    pattern_type=PatternType.FLAG,
                    pattern_name="Bull Flag" if consolidation.iloc[-1] < consolidation.mean() else "Bull Pennant",
                    bullish=True,
                    completion_pct=75,
                    breakout_level=float(high.iloc[10:].max()),
                    target_price=float(current_price * 1.15),
                    stop_loss=float(low.iloc[-10:].min() * 0.98),
                    confidence=0.65,
                    description=f"Sharp {first_move:.1f}% move with tight consolidation"
                ))

        return patterns

    def _detect_wedges(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect Rising and Falling Wedges."""
        patterns = []

        if len(df) < 30:
            return patterns

        lookback = min(40, len(df))
        data = df.tail(lookback)

        high = data["high"]
        low = data["low"]
        close = data["close"]

        # Calculate trendlines
        highs_trend = np.polyfit(range(len(high)), high.values, 1)
        lows_trend = np.polyfit(range(len(low)), low.values, 1)

        high_slope = highs_trend[0]
        low_slope = lows_trend[0]

        # Rising Wedge: both lines rising, but lows rising faster (bearish)
        if high_slope > 0 and low_slope > 0 and low_slope > high_slope * 1.5:
            patterns.append(PatternMatch(
                pattern_type=PatternType.WEDGE_RISING,
                pattern_name="Rising Wedge",
                bullish=False,
                completion_pct=70,
                breakout_level=float(low.iloc[-5:].min()),
                target_price=float(close.iloc[-1] * 0.9),
                stop_loss=float(high.iloc[-1] * 1.02),
                confidence=0.60,
                description="Converging upward lines - typically bearish"
            ))

        # Falling Wedge: both lines falling, highs falling faster (bullish)
        if high_slope < 0 and low_slope < 0 and high_slope < low_slope * 1.5:
            patterns.append(PatternMatch(
                pattern_type=PatternType.WEDGE_FALLING,
                pattern_name="Falling Wedge",
                bullish=True,
                completion_pct=70,
                breakout_level=float(high.iloc[-5:].max()),
                target_price=float(close.iloc[-1] * 1.15),
                stop_loss=float(low.iloc[-1] * 0.98),
                confidence=0.60,
                description="Converging downward lines - typically bullish"
            ))

        return patterns

    def _detect_base_breakout(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect base breakout pattern."""
        patterns = []

        if len(df) < 50:
            return patterns

        # Look for consolidation followed by breakout
        lookback = min(80, len(df))
        data = df.tail(lookback)

        close = data["close"]
        high = data["high"]
        volume = data["volume"] if "volume" in data.columns else None

        # Find consolidation zone
        base_high = high.iloc[:-10].max()
        base_low = data["low"].iloc[:-10].min()
        base_range = (base_high - base_low) / base_high * 100

        current_price = float(close.iloc[-1])

        # Check for breakout
        if base_range < 15 and current_price > base_high * 1.01:
            # Check volume confirmation
            vol_confirmed = False
            if volume is not None:
                avg_vol = volume.iloc[:-10].mean()
                recent_vol = volume.iloc[-5:].mean()
                vol_confirmed = recent_vol > avg_vol * 1.3

            confidence = 0.75 if vol_confirmed else 0.60

            patterns.append(PatternMatch(
                pattern_type=PatternType.BASE_BREAKOUT,
                pattern_name="Base Breakout",
                bullish=True,
                completion_pct=85,
                breakout_level=float(base_high),
                target_price=float(base_high + (base_high - base_low)),
                stop_loss=float(base_low * 0.98),
                confidence=confidence,
                description=f"Breaking out of {base_range:.1f}% base range"
            ))

        return patterns

    def _detect_high_tight_flag(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect High Tight Flag pattern."""
        patterns = []

        if len(df) < 40:
            return patterns

        lookback = min(60, len(df))
        data = df.tail(lookback)

        close = data["close"]
        high = data["high"]
        low = data["low"]

        # Look for 100%+ move in 4-8 weeks
        start_price = float(close.iloc[0])
        peak_price = float(high.iloc[:30].max())
        current_price = float(close.iloc[-1])

        price_gain = (peak_price - start_price) / start_price * 100

        if price_gain > 100:
            # Check for tight consolidation near highs
            recent_high = float(high.iloc[-15:].max())
            recent_low = float(low.iloc[-15:].min())
            consolidation_depth = (recent_high - recent_low) / recent_high * 100

            if consolidation_depth < 10 and current_price > peak_price * 0.9:
                patterns.append(PatternMatch(
                    pattern_type=PatternType.HIGH_TIGHT_FLAG,
                    pattern_name="High Tight Flag",
                    bullish=True,
                    completion_pct=80,
                    breakout_level=float(recent_high),
                    target_price=float(recent_high * 1.2),
                    stop_loss=float(recent_low * 0.97),
                    confidence=0.75,
                    description=f"100%+ gain with {consolidation_depth:.1f}% consolidation"
                ))

        return patterns

    def _detect_ma_pullback(self, df: pd.DataFrame) -> list[PatternMatch]:
        """Detect pullback to moving average entry."""
        patterns = []

        if len(df) < 100:
            return patterns

        close = df["close"]

        # Calculate key MAs
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()

        current_price = float(close.iloc[-1])
        ma_20 = float(sma_20.iloc[-1])
        ma_50 = float(sma_50.iloc[-1])

        # Check for pullback to 20 MA
        if abs(current_price - ma_20) / ma_20 < 0.02:
            # Check if trend is up
            if sma_20.iloc[-1] > sma_20.iloc[-20]:
                patterns.append(PatternMatch(
                    pattern_type=PatternType.PULLBACK_MA,
                    pattern_name="Pullback to 20 MA",
                    bullish=True,
                    completion_pct=85,
                    breakout_level=float(current_price * 1.02),
                    target_price=float(current_price * 1.1),
                    stop_loss=float(ma_20 * 0.97),
                    confidence=0.65,
                    description="Pullback to rising 20 MA in uptrend"
                ))

        # Check for pullback to 50 MA
        if abs(current_price - ma_50) / ma_50 < 0.02:
            if sma_50.iloc[-1] > sma_50.iloc[-30]:
                patterns.append(PatternMatch(
                    pattern_type=PatternType.PULLBACK_MA,
                    pattern_name="Pullback to 50 MA",
                    bullish=True,
                    completion_pct=85,
                    breakout_level=float(current_price * 1.02),
                    target_price=float(current_price * 1.1),
                    stop_loss=float(ma_50 * 0.96),
                    confidence=0.65,
                    description="Pullback to rising 50 MA in uptrend"
                ))

        return patterns

    def _find_pivots(self, df: pd.DataFrame, window: int = 5) -> list[dict]:
        """Find pivot points (swing highs and lows)."""
        pivots = []
        high = df["high"]
        low = df["low"]

        for i in range(window, len(df) - window):
            # Check for pivot high
            if all(high.iloc[i] >= high.iloc[i - j] for j in range(1, window + 1)) and \
               all(high.iloc[i] >= high.iloc[i + j] for j in range(1, window + 1)):
                pivots.append({"type": "high", "high": float(high.iloc[i]), "low": float(low.iloc[i])})

            # Check for pivot low
            if all(low.iloc[i] <= low.iloc[i - j] for j in range(1, window + 1)) and \
               all(low.iloc[i] <= low.iloc[i + j] for j in range(1, window + 1)):
                pivots.append({"type": "low", "high": float(high.iloc[i]), "low": float(low.iloc[i])})

        return pivots

    def _find_peaks(self, series: pd.Series, window: int = 5) -> list[int]:
        """Find indices of peaks in series."""
        peaks = []
        for i in range(window, len(series) - window):
            if all(series.iloc[i] >= series.iloc[i - j] for j in range(1, window + 1)) and \
               all(series.iloc[i] >= series.iloc[i + j] for j in range(1, window + 1)):
                peaks.append(i)
        return peaks

    def _find_troughs(self, series: pd.Series, window: int = 5) -> list[int]:
        """Find indices of troughs in series."""
        troughs = []
        for i in range(window, len(series) - window):
            if all(series.iloc[i] <= series.iloc[i - j] for j in range(1, window + 1)) and \
               all(series.iloc[i] <= series.iloc[i + j] for j in range(1, window + 1)):
                troughs.append(i)
        return troughs
