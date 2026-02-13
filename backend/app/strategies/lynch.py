"""Peter Lynch GARP (Growth at Reasonable Price) Strategy.

Note: This is a simplified implementation focusing on technical aspects.
Full implementation would require fundamental data (P/E, earnings growth, etc.)
which is not readily available through yfinance for Indian stocks.
"""

from typing import Optional

import pandas as pd

from app.strategies.base import BaseStrategy, StrategyResult


class LynchStrategy(BaseStrategy):
    """Peter Lynch's GARP Approach - Adapted for Technical Analysis.

    Key principles adapted for technical analysis:
    1. Buy what you know (focus on established companies)
    2. Look for consistent growth patterns
    3. Buy on pullbacks to support
    4. Long-term trend following
    5. Position sizing based on conviction

    Scoring (simplified for technical focus):
    - Trend Consistency: 0-30 points
    - Pullback Quality: 0-25 points
    - Volume Patterns: 0-20 points
    - Momentum: 0-15 points
    - Volatility: 0-10 points
    Total: 0-100 points
    """

    name = "Lynch GARP Approach"
    description = "Peter Lynch's growth at reasonable price approach (technical adaptation)"

    def analyze(self, df: pd.DataFrame, indicators: dict) -> StrategyResult:
        """Analyze stock using Lynch principles (technical adaptation)."""
        if df.empty or len(df) < 100:
            return StrategyResult(
                score=0,
                bullish_factors=[],
                bearish_factors=["Insufficient data"],
                warnings=["Need at least 100 bars for analysis"],
                signal="AVOID",
                conviction="LOW"
            )

        bullish_factors = []
        bearish_factors = []
        warnings = []

        # Calculate scores
        trend_score = self._score_trend_consistency(df, indicators, bullish_factors, bearish_factors)
        pullback_score = self._score_pullback_quality(df, indicators, bullish_factors, bearish_factors, warnings)
        volume_score = self._score_volume_patterns(df, indicators, bullish_factors, bearish_factors, warnings)
        momentum_score = self._score_momentum(df, indicators, bullish_factors, bearish_factors, warnings)
        volatility_score = self._score_volatility(df, indicators, bullish_factors, warnings)

        total_score = trend_score + pullback_score + volume_score + momentum_score + volatility_score

        signal, conviction = self._get_signal_from_score(total_score)

        return StrategyResult(
            score=total_score,
            bullish_factors=bullish_factors,
            bearish_factors=bearish_factors,
            warnings=warnings,
            signal=signal,
            conviction=conviction
        )

    def _score_trend_consistency(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        bearish: list,
    ) -> float:
        """Score trend consistency (Lynch preferred consistent growers).

        Score: 0-30 points
        """
        score = 0.0

        if len(df) < 100:
            return 0

        close = df["close"]

        # Check long-term trend (200-day)
        sma_200 = close.rolling(window=200).mean()
        if not sma_200.empty:
            current_sma_200 = float(sma_200.iloc[-1])
            price_100_ago = float(close.iloc[-100])
            sma_200_100_ago = float(sma_200.iloc[-100]) if len(sma_200) > 100 else current_sma_200

            # Consistent uptrend
            if current_sma_200 > sma_200_100_ago:
                score += 15
                bullish.append("Long-term uptrend intact")
            else:
                bearish.append("Long-term trend weakening")

        # Check for consistent price appreciation
        # Lynch liked stocks that steadily increased
        monthly_returns = close.pct_change(20).dropna()  # ~monthly returns
        if len(monthly_returns) >= 6:
            positive_months = sum(1 for r in monthly_returns.tail(6) if r > 0)
            if positive_months >= 5:
                score += 10
                bullish.append(f"Consistent gains ({positive_months}/6 months positive)")
            elif positive_months >= 4:
                score += 6
            elif positive_months <= 2:
                bearish.append(f"Inconsistent performance ({positive_months}/6 months positive)")

        # Price vs long-term MA
        current_price = float(close.iloc[-1])
        sma_200 = self._safe_get(indicators, "sma_200")

        if sma_200:
            if current_price > sma_200:
                score += 5
                bullish.append("Trading above 200-day MA")

        return min(30, score)

    def _score_pullback_quality(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        bearish: list,
        warnings: list,
    ) -> float:
        """Score pullback quality (Lynch liked buying on pullbacks).

        Score: 0-25 points
        """
        score = 0.0

        close = df["close"]
        current_price = float(close.iloc[-1])

        # Get support levels
        sma_50 = self._safe_get(indicators, "sma_50")
        sma_200 = self._safe_get(indicators, "sma_200")

        # Check if at or near support
        if sma_50:
            distance_to_50ma = abs(current_price - sma_50) / sma_50 * 100

            if distance_to_50ma < 3:
                score += 12
                bullish.append("At/near 50-day MA support (good pullback entry)")
            elif distance_to_50ma < 5:
                score += 8
                bullish.append("Close to 50-day MA support")
            elif current_price > sma_50 * 1.15:
                warnings.append("Extended far above 50-day MA")
            elif current_price < sma_50:
                bearish.append("Below 50-day MA")

        # Check 200-day MA support
        if sma_200:
            distance_to_200ma = abs(current_price - sma_200) / sma_200 * 100

            if distance_to_200ma < 5 and current_price > sma_200:
                score += 8
                bullish.append("Near 200-day MA support")

        # Check recent pullback depth
        if len(close) >= 30:
            recent_high = close.tail(30).max()
            pullback_pct = (recent_high - current_price) / recent_high * 100

            if 5 < pullback_pct < 15:
                score += 5
                bullish.append(f"Healthy pullback ({pullback_pct:.1f}% from recent high)")
            elif pullback_pct > 20:
                bearish.append(f"Deep pullback ({pullback_pct:.1f}% from recent high)")
            elif pullback_pct < 3:
                warnings.append("Minimal pullback - may be extended")

        return min(25, score)

    def _score_volume_patterns(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        bearish: list,
        warnings: list,
    ) -> float:
        """Score volume patterns.

        Score: 0-20 points
        """
        score = 0.0

        if "volume" not in df.columns:
            return 0

        volume = df["volume"]

        # Average volumes
        vol_sma_20 = self._safe_get(indicators, "volume_sma_20")
        vol_sma_50 = self._safe_get(indicators, "volume_sma_50")

        if vol_sma_20 and vol_sma_50:
            # Volume should be healthy but not extreme
            ratio = vol_sma_20 / vol_sma_50

            if 0.9 < ratio < 1.3:
                score += 8
                bullish.append("Healthy volume levels")
            elif ratio < 0.7:
                warnings.append("Volume declining - may indicate lack of interest")
            elif ratio > 1.5:
                score += 5
                bullish.append("Increasing volume")

        # Check for accumulation (higher volume on up days)
        recent = df.tail(20)
        up_days = recent[recent["close"] > recent["open"]]
        down_days = recent[recent["close"] < recent["open"]]

        if len(up_days) > 0 and len(down_days) > 0:
            up_vol = up_days["volume"].mean()
            down_vol = down_days["volume"].mean()

            if up_vol > down_vol * 1.2:
                score += 12
                bullish.append("Accumulation pattern (volume on up days)")
            elif down_vol > up_vol * 1.2:
                bearish.append("Distribution pattern (volume on down days)")
            else:
                score += 6

        return min(20, score)

    def _score_momentum(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        bearish: list,
        warnings: list,
    ) -> float:
        """Score momentum indicators.

        Score: 0-15 points
        """
        score = 0.0

        # RSI
        rsi = self._safe_get(indicators, "rsi_14")
        if rsi is not None:
            if 40 < rsi < 70:
                score += 6
                bullish.append(f"RSI in bullish zone ({rsi:.1f})")
            elif rsi >= 70:
                warnings.append(f"RSI overbought ({rsi:.1f})")
            elif rsi <= 30:
                bearish.append(f"RSI oversold ({rsi:.1f})")
            else:
                score += 3

        # MACD
        macd = self._safe_get(indicators, "macd")
        macd_signal = self._safe_get(indicators, "macd_signal")
        macd_hist = self._safe_get(indicators, "macd_histogram")

        if macd is not None and macd_signal is not None:
            if macd > macd_signal and macd > 0:
                score += 5
                bullish.append("MACD bullish and positive")
            elif macd > macd_signal:
                score += 3
                bullish.append("MACD bullish crossover")
            elif macd < macd_signal and macd < 0:
                bearish.append("MACD bearish")

        # Stochastic
        stoch_k = self._safe_get(indicators, "stoch_k")
        if stoch_k is not None:
            if 20 < stoch_k < 80:
                score += 4
            elif stoch_k >= 80:
                warnings.append("Stochastic overbought")
            elif stoch_k <= 20:
                bullish.append("Stochastic oversold - potential bounce")

        return min(15, score)

    def _score_volatility(
        self,
        df: pd.DataFrame,
        indicators: dict,
        bullish: list,
        warnings: list,
    ) -> float:
        """Score volatility (Lynch preferred lower volatility growers).

        Score: 0-10 points
        """
        score = 0.0

        close = df["close"]

        # Calculate historical volatility
        returns = close.pct_change().dropna()
        if len(returns) >= 20:
            volatility = returns.tail(20).std() * 100  # Daily vol as %

            # Annualized
            ann_vol = volatility * (252 ** 0.5)

            if ann_vol < 25:
                score += 10
                bullish.append("Low volatility - consistent performer")
            elif ann_vol < 35:
                score += 7
                bullish.append("Moderate volatility")
            elif ann_vol > 50:
                warnings.append(f"High volatility ({ann_vol:.1f}% annualized)")
                score += 2
            else:
                score += 4

        # ATR-based volatility
        atr = self._safe_get(indicators, "atr_14")
        if atr is not None:
            current_price = float(close.iloc[-1])
            atr_pct = (atr / current_price) * 100

            if atr_pct < 2:
                score += 5
            elif atr_pct > 4:
                score -= 2

        return max(0, min(10, score))
