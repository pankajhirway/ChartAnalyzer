"""Base strategy class for all trading strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from app.models.analysis import TrendType, WeinsteinStage


@dataclass
class StrategyResult:
    """Result from a strategy analysis."""
    score: float  # 0-100
    bullish_factors: list[str]
    bearish_factors: list[str]
    warnings: list[str]
    signal: str  # BUY, SELL, HOLD, AVOID
    conviction: str  # HIGH, MEDIUM, LOW


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""

    name: str = "Base Strategy"
    description: str = "Base strategy class"

    @abstractmethod
    def analyze(self, df: pd.DataFrame, indicators: dict) -> StrategyResult:
        """Analyze price data and return strategy result.

        Args:
            df: DataFrame with OHLCV data
            indicators: Dictionary of calculated indicators

        Returns:
            StrategyResult with score and analysis
        """
        pass

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
