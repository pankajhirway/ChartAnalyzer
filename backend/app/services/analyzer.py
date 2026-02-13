"""Main analysis orchestrator service."""

from datetime import datetime
from typing import Optional

import pandas as pd
import structlog

from app.analysis.indicators import TechnicalIndicators
from app.analysis.patterns import PatternDetector
from app.analysis.support_resistance import SupportResistanceDetector
from app.analysis.trend_analysis import TrendAnalyzer
from app.analysis.volume_analysis import VolumeAnalyzer
from app.core.yfinance_provider import YFinanceProvider
from app.models.stock import PriceData
from app.models.analysis import (
    AnalysisResult,
    TrendType,
    WeinsteinStage,
    Level,
    PatternMatch,
    Indicators,
    StrategyScores,
    SignalType,
    ConvictionLevel,
)
from app.models.trade import TradeSuggestion, EntryZone, Target, StopLossType, HoldingPeriod
from app.strategies.composite import CompositeStrategy

logger = structlog.get_logger()


class AnalyzerService:
    """Main analysis orchestrator service.

    Coordinates all analysis components to produce a complete
    analysis result with trade suggestions.
    """

    def __init__(self):
        """Initialize analyzer with all components."""
        self.data_provider = YFinanceProvider()
        self.indicators = TechnicalIndicators()
        self.pattern_detector = PatternDetector()
        self.sr_detector = SupportResistanceDetector()
        self.trend_analyzer = TrendAnalyzer()
        self.volume_analyzer = VolumeAnalyzer()
        self.strategy = CompositeStrategy()

    async def analyze(
        self,
        symbol: str,
        timeframe: str = "1d",
    ) -> Optional[AnalysisResult]:
        """Perform complete analysis on a stock.

        Args:
            symbol: Stock symbol
            timeframe: Data timeframe

        Returns:
            Complete AnalysisResult or None if analysis fails
        """
        try:
            # Fetch data
            price_data = await self.data_provider.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
            )

            if not price_data or len(price_data) < 100:
                logger.warning("Insufficient data for analysis", symbol=symbol)
                return None

            # Convert to DataFrame
            df = self._price_data_to_df(price_data)

            # Get stock info
            stock_info = await self.data_provider.get_stock_info(symbol)
            company_name = stock_info.company_name if stock_info else None

            # Calculate indicators
            indicator_values = self.indicators.calculate_all(df)
            indicator_dict = self._indicators_to_dict(indicator_values)

            # Analyze trend
            trend, trend_strength, trend_notes = self.trend_analyzer.analyze_trend(df)

            # Determine Weinstein stage
            stage, stage_desc = self.trend_analyzer.determine_weinstein_stage(df)

            # Detect patterns
            patterns = self.pattern_detector.detect_patterns(df)

            # Detect support/resistance
            support, resistance = self.sr_detector.detect_levels(df)

            # Analyze volume
            volume_analysis = self.volume_analyzer.analyze_volume(df)

            # Run composite strategy
            strategy_result = await self.strategy.analyze(df, indicator_dict, symbol)

            # Generate trade suggestion
            trade_suggestion = self._generate_trade_suggestion(
                symbol=symbol,
                df=df,
                indicators=indicator_values,
                patterns=patterns,
                support=support,
                resistance=resistance,
                strategy_result=strategy_result,
            )

            # Build analysis factors
            bullish_factors = strategy_result.bullish_factors[:5]
            bearish_factors = strategy_result.bearish_factors[:5]
            warnings = strategy_result.warnings[:3]

            # Add volume notes
            if volume_analysis.get("accumulation_detected"):
                bullish_factors.append("Volume shows accumulation")
            if volume_analysis.get("on_breakout"):
                bullish_factors.append("Breakout volume detected")

            # Create result
            result = AnalysisResult(
                symbol=symbol.upper(),
                company_name=company_name,
                timestamp=datetime.now(),
                timeframe=timeframe,
                current_price=float(df["close"].iloc[-1]),
                primary_trend=trend,
                trend_strength=trend_strength,
                trend_notes=trend_notes,
                weinstein_stage=stage,
                stage_description=stage_desc,
                scores=strategy_result.scores,
                detected_patterns=patterns,
                support_levels=support,
                resistance_levels=resistance,
                signal=strategy_result.signal,
                conviction=strategy_result.conviction,
                indicators=indicator_values,
                bullish_factors=bullish_factors,
                bearish_factors=bearish_factors,
                warnings=warnings,
            )

            logger.info(
                "Analysis completed",
                symbol=symbol,
                composite_score=strategy_result.scores.composite_score,
                signal=strategy_result.signal.value,
            )

            return result

        except Exception as e:
            logger.error("Analysis failed", symbol=symbol, error=str(e))
            return None

    def _price_data_to_df(self, price_data: list[PriceData]) -> pd.DataFrame:
        """Convert price data list to DataFrame."""
        data = []
        for p in price_data:
            data.append({
                "timestamp": p.timestamp,
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume,
            })

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def _indicators_to_dict(self, indicators: Indicators) -> dict:
        """Convert Indicators model to dictionary."""
        return {
            k: v for k, v in indicators.model_dump().items()
            if v is not None
        }

    def _generate_trade_suggestion(
        self,
        symbol: str,
        df: pd.DataFrame,
        indicators: Indicators,
        patterns: list[PatternMatch],
        support: list[Level],
        resistance: list[Level],
        strategy_result,
    ) -> Optional[TradeSuggestion]:
        """Generate trade suggestion based on analysis."""
        current_price = float(df["close"].iloc[-1])

        # Only generate trade suggestion for BUY or SELL signals
        if strategy_result.signal == SignalType.HOLD:
            return None

        if strategy_result.signal == SignalType.AVOID:
            return TradeSuggestion(
                symbol=symbol.upper(),
                timestamp=datetime.now(),
                action=SignalType.AVOID,
                conviction=strategy_result.conviction,
                entry_price=current_price,
                entry_zone=EntryZone(low=current_price * 0.99, high=current_price * 1.01),
                entry_trigger="Do not enter - wait for better setup",
                stop_loss=current_price * 1.05,
                stop_loss_type=StopLossType.PERCENTAGE,
                stop_loss_pct=5.0,
                risk_per_share=current_price * 0.05,
                target_1=Target(price=current_price, risk_reward=0, description="N/A"),
                target_2=Target(price=current_price, risk_reward=0, description="N/A"),
                target_3=Target(price=current_price, risk_reward=0, description="N/A"),
                suggested_position_pct=0,
                max_position_pct=0,
                risk_reward_ratio=0,
                holding_period=HoldingPeriod.SWING,
                strategy_source="Composite Strategy",
                reasoning=["Current setup not favorable"] + strategy_result.bearish_factors[:3],
                warnings=strategy_result.warnings,
            )

        # Calculate entry, stop, and targets for BUY signals
        atr = indicators.atr_14 or current_price * 0.02

        # Entry zone
        entry_price = current_price
        entry_low = current_price - atr * 0.5
        entry_high = current_price + atr * 0.5

        # Use nearest support for stop loss
        if support:
            stop_loss = max(s.price for s in support[:3]) - atr * 0.5
        else:
            stop_loss = current_price - atr * 2

        # Ensure stop is below entry
        stop_loss = min(stop_loss, current_price - atr * 1.5)

        # Calculate risk
        risk_per_share = entry_price - stop_loss
        stop_pct = (risk_per_share / entry_price) * 100

        # Calculate targets
        target_1_price = entry_price + risk_per_share * 1.5
        target_2_price = entry_price + risk_per_share * 2.5
        target_3_price = entry_price + risk_per_share * 4.0

        # Use resistance for target adjustment
        if resistance:
            nearest_resistance = min(resistance, key=lambda x: abs(x.price - entry_price))
            if entry_price < nearest_resistance.price < target_2_price:
                target_2_price = nearest_resistance.price * 0.98

        # Position sizing based on conviction
        position_pct = {
            ConvictionLevel.HIGH: 5.0,
            ConvictionLevel.MEDIUM: 3.0,
            ConvictionLevel.LOW: 1.5,
        }.get(strategy_result.conviction, 2.0)

        # Entry trigger description
        entry_trigger = "Current price level"
        if patterns:
            primary_pattern = patterns[0]
            if primary_pattern.breakout_level:
                entry_trigger = f"Buy on breakout above {primary_pattern.breakout_level:.2f}"

        # Build reasoning
        reasoning = []
        if patterns:
            reasoning.append(f"Pattern: {patterns[0].pattern_name}")
        reasoning.extend(strategy_result.bullish_factors[:4])

        return TradeSuggestion(
            symbol=symbol.upper(),
            timestamp=datetime.now(),
            action=strategy_result.signal,
            conviction=strategy_result.conviction,
            entry_price=round(entry_price, 2),
            entry_zone=EntryZone(low=round(entry_low, 2), high=round(entry_high, 2)),
            entry_trigger=entry_trigger,
            stop_loss=round(stop_loss, 2),
            stop_loss_type=StopLossType.SUPPORT if support else StopLossType.ATR,
            stop_loss_pct=round(stop_pct, 2),
            risk_per_share=round(risk_per_share, 2),
            target_1=Target(
                price=round(target_1_price, 2),
                risk_reward=1.5,
                description="Conservative target"
            ),
            target_2=Target(
                price=round(target_2_price, 2),
                risk_reward=2.5,
                description="Moderate target"
            ),
            target_3=Target(
                price=round(target_3_price, 2),
                risk_reward=4.0,
                description="Aggressive target"
            ),
            suggested_position_pct=position_pct,
            max_position_pct=position_pct * 1.5,
            risk_reward_ratio=2.0,
            holding_period=HoldingPeriod.SWING,
            strategy_source="Composite: Minervini + Weinstein + Lynch",
            reasoning=reasoning,
            warnings=strategy_result.warnings,
        )

    async def get_indicators_only(
        self,
        symbol: str,
        timeframe: str = "1d",
    ) -> Optional[Indicators]:
        """Get just the technical indicators for a stock."""
        price_data = await self.data_provider.get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
        )

        if not price_data or len(price_data) < 50:
            return None

        df = self._price_data_to_df(price_data)
        return self.indicators.calculate_all(df)
