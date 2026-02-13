"""Technical indicators calculation engine."""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from app.models.analysis import Indicators


@dataclass
class IndicatorConfig:
    """Configuration for indicator calculations."""
    sma_periods: list[int] = None
    ema_periods: list[int] = None
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    rsi_period: int = 14
    stoch_k: int = 14
    stoch_d: int = 3
    bb_period: int = 20
    bb_std: float = 2.0
    atr_period: int = 14
    adx_period: int = 14
    volume_sma_periods: list[int] = None

    def __post_init__(self):
        if self.sma_periods is None:
            self.sma_periods = [10, 20, 50, 150, 200]
        if self.ema_periods is None:
            self.ema_periods = [8, 21]
        if self.volume_sma_periods is None:
            self.volume_sma_periods = [20, 50]


class TechnicalIndicators:
    """Technical indicators calculation class.

    Provides methods to calculate various technical indicators
    for stock analysis.
    """

    def __init__(self, config: Optional[IndicatorConfig] = None):
        """Initialize with optional configuration.

        Args:
            config: Indicator configuration settings
        """
        self.config = config or IndicatorConfig()

    def calculate_all(self, df: pd.DataFrame) -> Indicators:
        """Calculate all technical indicators.

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)

        Returns:
            Indicators model with all calculated values
        """
        if df.empty or len(df) < 50:
            return Indicators()

        indicators = {}

        # Moving Averages
        ma_indicators = self._calculate_moving_averages(df)
        indicators.update(ma_indicators)

        # MACD
        macd_indicators = self._calculate_macd(df)
        indicators.update(macd_indicators)

        # RSI
        indicators["rsi_14"] = self._calculate_rsi(df["close"])

        # Stochastic
        stoch_indicators = self._calculate_stochastic(df)
        indicators.update(stoch_indicators)

        # Bollinger Bands
        bb_indicators = self._calculate_bollinger_bands(df)
        indicators.update(bb_indicators)

        # ATR
        indicators["atr_14"] = self._calculate_atr(df)

        # ADX
        adx_indicators = self._calculate_adx(df)
        indicators.update(adx_indicators)

        # Volume indicators
        volume_indicators = self._calculate_volume_indicators(df)
        indicators.update(volume_indicators)

        return Indicators(**indicators)

    def _calculate_moving_averages(self, df: pd.DataFrame) -> dict:
        """Calculate all moving averages."""
        close = df["close"]
        indicators = {}

        # SMAs
        for period in self.config.sma_periods:
            if len(close) >= period:
                indicators[f"sma_{period}"] = float(close.rolling(window=period).mean().iloc[-1])

        # EMAs
        for period in self.config.ema_periods:
            if len(close) >= period:
                indicators[f"ema_{period}"] = float(close.ewm(span=period, adjust=False).mean().iloc[-1])

        return indicators

    def _calculate_macd(self, df: pd.DataFrame) -> dict:
        """Calculate MACD indicator."""
        close = df["close"]
        exp1 = close.ewm(span=self.config.macd_fast, adjust=False).mean()
        exp2 = close.ewm(span=self.config.macd_slow, adjust=False).mean()

        macd = exp1 - exp2
        signal = macd.ewm(span=self.config.macd_signal, adjust=False).mean()
        histogram = macd - signal

        return {
            "macd": float(macd.iloc[-1]) if not macd.empty else None,
            "macd_signal": float(signal.iloc[-1]) if not signal.empty else None,
            "macd_histogram": float(histogram.iloc[-1]) if not histogram.empty else None,
        }

    def _calculate_rsi(self, close: pd.Series) -> Optional[float]:
        """Calculate RSI indicator."""
        period = self.config.rsi_period

        if len(close) < period + 1:
            return None

        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1]) if not rsi.empty else None

    def _calculate_stochastic(self, df: pd.DataFrame) -> dict:
        """Calculate Stochastic oscillator."""
        period = self.config.stoch_k
        smooth_k = 3
        smooth_d = self.config.stoch_d

        if len(df) < period:
            return {"stoch_k": None, "stoch_d": None}

        low_min = df["low"].rolling(window=period).min()
        high_max = df["high"].rolling(window=period).max()

        k = 100 * ((df["close"] - low_min) / (high_max - low_min).replace(0, np.inf))
        k = k.rolling(window=smooth_k).mean()
        d = k.rolling(window=smooth_d).mean()

        return {
            "stoch_k": float(k.iloc[-1]) if not k.empty else None,
            "stoch_d": float(d.iloc[-1]) if not d.empty else None,
        }

    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> dict:
        """Calculate Bollinger Bands."""
        period = self.config.bb_period
        std_dev = self.config.bb_std

        if len(df) < period:
            return {"bb_upper": None, "bb_middle": None, "bb_lower": None, "bb_width": None}

        close = df["close"]
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        # Band width (as percentage of middle band)
        width = ((upper - lower) / middle) * 100

        return {
            "bb_upper": float(upper.iloc[-1]) if not upper.empty else None,
            "bb_middle": float(middle.iloc[-1]) if not middle.empty else None,
            "bb_lower": float(lower.iloc[-1]) if not lower.empty else None,
            "bb_width": float(width.iloc[-1]) if not width.empty else None,
        }

    def _calculate_atr(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate Average True Range."""
        period = self.config.atr_period

        if len(df) < period + 1:
            return None

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return float(atr.iloc[-1]) if not atr.empty else None

    def _calculate_adx(self, df: pd.DataFrame) -> dict:
        """Calculate ADX and Directional Indicators."""
        period = self.config.adx_period

        if len(df) < period * 2:
            return {"adx_14": None, "plus_di": None, "minus_di": None}

        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Smooth the values
        atr = true_range.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.inf)
        adx = dx.rolling(window=period).mean()

        return {
            "adx_14": float(adx.iloc[-1]) if not adx.empty else None,
            "plus_di": float(plus_di.iloc[-1]) if not plus_di.empty else None,
            "minus_di": float(minus_di.iloc[-1]) if not minus_di.empty else None,
        }

    def _calculate_volume_indicators(self, df: pd.DataFrame) -> dict:
        """Calculate volume-based indicators."""
        volume = df["volume"]
        close = df["close"]
        indicators = {}

        # Volume SMAs
        for period in self.config.volume_sma_periods:
            if len(volume) >= period:
                indicators[f"volume_sma_{period}"] = float(volume.rolling(window=period).mean().iloc[-1])

        # OBV (On-Balance Volume)
        direction = np.sign(close.diff()).fillna(0)
        obv = (volume * direction).cumsum()
        indicators["obv"] = float(obv.iloc[-1]) if not obv.empty else None

        # OBV SMA
        if len(obv) >= 20:
            indicators["obv_sma"] = float(obv.rolling(window=20).mean().iloc[-1])

        return indicators

    def calculate_relative_strength(
        self,
        stock_close: pd.Series,
        benchmark_close: pd.Series,
    ) -> Optional[float]:
        """Calculate relative strength vs benchmark.

        Args:
            stock_close: Stock closing prices
            benchmark_close: Benchmark (e.g., Nifty) closing prices

        Returns:
            Relative strength ratio
        """
        if stock_close.empty or benchmark_close.empty:
            return None

        # Align the series
        stock_close = stock_close.dropna()
        benchmark_close = benchmark_close.dropna()

        if len(stock_close) < 2 or len(benchmark_close) < 2:
            return None

        # Calculate relative strength as ratio of percent changes
        stock_change = stock_close.iloc[-1] / stock_close.iloc[0]
        benchmark_change = benchmark_close.iloc[-1] / benchmark_close.iloc[0]

        return float(stock_change / benchmark_change) if benchmark_change else None

    def get_ma_alignment(self, df: pd.DataFrame) -> dict:
        """Analyze moving average alignment.

        Returns information about MA alignment which is important
        for Minervini setup criteria.
        """
        close = df["close"]
        current_price = float(close.iloc[-1])

        sma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None
        sma_150 = close.rolling(window=150).mean().iloc[-1] if len(close) >= 150 else None
        sma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else None

        result = {
            "price_above_sma50": None,
            "price_above_sma150": None,
            "price_above_sma200": None,
            "sma50_above_sma150": None,
            "sma50_above_sma200": None,
            "sma150_above_sma200": None,
            "perfect_alignment": False,
        }

        if sma_50 is not None:
            result["price_above_sma50"] = current_price > sma_50

        if sma_150 is not None:
            result["price_above_sma150"] = current_price > sma_150

        if sma_200 is not None:
            result["price_above_sma200"] = current_price > sma_200

        if sma_50 is not None and sma_150 is not None:
            result["sma50_above_sma150"] = sma_50 > sma_150

        if sma_50 is not None and sma_200 is not None:
            result["sma50_above_sma200"] = sma_50 > sma_200

        if sma_150 is not None and sma_200 is not None:
            result["sma150_above_sma200"] = sma_150 > sma_200

        # Perfect alignment: Price > SMA50 > SMA150 > SMA200
        if all([
            result["price_above_sma50"],
            result["price_above_sma150"],
            result["price_above_sma200"],
            result["sma50_above_sma150"],
            result["sma150_above_sma200"],
        ]):
            result["perfect_alignment"] = True

        return result

    def get_ma_slope_status(self, df: pd.DataFrame, lookback: int = 20) -> dict:
        """Get moving average slope status.

        Important for determining if MAs are trending up/down.
        """
        close = df["close"]
        result = {}

        for period in [50, 150, 200]:
            if len(close) >= period + lookback:
                sma = close.rolling(window=period).mean()
                slope = (sma.iloc[-1] - sma.iloc[-lookback]) / sma.iloc[-lookback] * 100
                result[f"sma{period}_slope"] = float(slope)
                result[f"sma{period}_rising"] = slope > 0

        return result
