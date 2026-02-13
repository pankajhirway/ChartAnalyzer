"""Helper utility functions."""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return data.rolling(window=period).mean()


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD, Signal, and Histogram."""
    ema_fast = data.ewm(span=fast_period, adjust=False).mean()
    ema_slow = data.ewm(span=slow_period, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram


def calculate_bollinger_bands(
    data: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands."""
    middle = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Calculate Average True Range."""
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()


def calculate_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator."""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    return k, d


def calculate_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate ADX, +DI, and -DI."""
    plus_dm = high.diff()
    minus_dm = low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0

    tr = calculate_atr(high, low, close, 1)
    atr = tr.rolling(window=period).mean()

    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (abs(minus_dm).rolling(window=period).mean() / atr)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()

    return adx, plus_di, minus_di


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate On-Balance Volume."""
    direction = np.where(close > close.shift(), 1, np.where(close < close.shift(), -1, 0))
    return (volume * direction).cumsum()


def find_swing_points(
    data: pd.Series,
    window: int = 5,
) -> tuple[list[int], list[int]]:
    """Find swing high and swing low points.

    Returns:
        Tuple of (swing_high_indices, swing_low_indices)
    """
    highs = []
    lows = []

    for i in range(window, len(data) - window):
        # Check for swing high
        if all(data.iloc[i] >= data.iloc[i - j] for j in range(1, window + 1)) and \
           all(data.iloc[i] >= data.iloc[i + j] for j in range(1, window + 1)):
            highs.append(i)

        # Check for swing low
        if all(data.iloc[i] <= data.iloc[i - j] for j in range(1, window + 1)) and \
           all(data.iloc[i] <= data.iloc[i + j] for j in range(1, window + 1)):
            lows.append(i)

    return highs, lows


def is_above_ma(close: float, ma: float) -> bool:
    """Check if price is above moving average."""
    return close > ma


def ma_slope(ma_values: pd.Series, periods: int = 5) -> float:
    """Calculate moving average slope.

    Returns:
        Positive for rising, negative for falling
    """
    if len(ma_values) < periods:
        return 0.0
    recent = ma_values.iloc[-periods:]
    return (recent.iloc[-1] - recent.iloc[0]) / periods


def percentage_from_high(close: float, period_high: float) -> float:
    """Calculate percentage below period high."""
    if period_high == 0:
        return 0.0
    return ((period_high - close) / period_high) * 100


def percentage_from_low(close: float, period_low: float) -> float:
    """Calculate percentage above period low."""
    if period_low == 0:
        return 0.0
    return ((close - period_low) / period_low) * 100


def volume_ratio(current_volume: int, avg_volume: float) -> float:
    """Calculate volume ratio vs average."""
    if avg_volume == 0:
        return 0.0
    return current_volume / avg_volume


def format_currency(value: float) -> str:
    """Format value as Indian currency."""
    if value >= 10000000:  # 1 crore
        return f"₹{value / 10000000:.2f} Cr"
    elif value >= 100000:  # 1 lakh
        return f"₹{value / 100000:.2f} L"
    else:
        return f"₹{value:,.2f}"


def timeframe_to_days(timeframe: str) -> int:
    """Convert timeframe string to approximate days."""
    mapping = {
        "1m": 0,
        "5m": 0,
        "15m": 0,
        "30m": 0,
        "1h": 0,
        "1d": 1,
        "1w": 7,
        "1M": 30,
    }
    return mapping.get(timeframe, 1)


def get_date_range(
    timeframe: str,
    bars: int = 500,
) -> tuple[datetime, datetime]:
    """Get date range for fetching data.

    Args:
        timeframe: Data timeframe
        bars: Number of bars needed

    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = datetime.now()

    # Calculate start date based on timeframe and bars needed
    if timeframe in ["1m", "5m", "15m", "30m"]:
        # Intraday - limited to 60 days
        start_date = end_date - timedelta(days=min(59, bars))
    elif timeframe == "1h":
        start_date = end_date - timedelta(days=min(365, bars // 6))
    elif timeframe == "1d":
        start_date = end_date - timedelta(days=bars * 2)  # Extra for weekends
    elif timeframe == "1w":
        start_date = end_date - timedelta(weeks=bars)
    else:
        start_date = end_date - timedelta(days=bars * 2)

    return start_date, end_date
