"""Analysis API routes."""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from app.services.analyzer import AnalyzerService
from app.models.analysis import AnalysisResult, Indicators, PatternMatch, Level

router = APIRouter()
analyzer = AnalyzerService()


@router.post("/{symbol}", response_model=AnalysisResult)
async def analyze_stock(
    symbol: str,
    timeframe: str = Query("1d", description="Analysis timeframe"),
):
    """Perform complete analysis on a stock.

    This endpoint runs the full analysis pipeline including:
    - Technical indicators calculation
    - Trend analysis
    - Pattern detection
    - Support/Resistance levels
    - Strategy scoring (Minervini, Weinstein, Lynch)
    - Trade suggestion generation
    """
    result = await analyzer.analyze(symbol.upper(), timeframe)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Analysis failed - insufficient data or stock not found"
        )

    return result


@router.get("/{symbol}/indicators", response_model=Indicators)
async def get_indicators(
    symbol: str,
    timeframe: str = Query("1d", description="Data timeframe"),
):
    """Get technical indicators for a stock."""
    indicators = await analyzer.get_indicators_only(symbol.upper(), timeframe)

    if not indicators:
        raise HTTPException(
            status_code=404,
            detail="Could not calculate indicators - insufficient data"
        )

    return indicators


@router.get("/{symbol}/patterns", response_model=list[PatternMatch])
async def get_patterns(
    symbol: str,
    timeframe: str = Query("1d", description="Data timeframe"),
):
    """Get detected chart patterns for a stock."""
    result = await analyzer.analyze(symbol.upper(), timeframe)

    if not result:
        raise HTTPException(status_code=404, detail="Analysis failed")

    return result.detected_patterns


@router.get("/{symbol}/levels")
async def get_levels(
    symbol: str,
    timeframe: str = Query("1d", description="Data timeframe"),
):
    """Get support and resistance levels for a stock."""
    result = await analyzer.analyze(symbol.upper(), timeframe)

    if not result:
        raise HTTPException(status_code=404, detail="Analysis failed")

    return {
        "symbol": symbol.upper(),
        "current_price": result.current_price,
        "support": result.support_levels,
        "resistance": result.resistance_levels,
    }


@router.get("/{symbol}/signals")
async def get_signals(
    symbol: str,
    timeframe: str = Query("1d", description="Data timeframe"),
):
    """Get trading signals for a stock."""
    result = await analyzer.analyze(symbol.upper(), timeframe)

    if not result:
        raise HTTPException(status_code=404, detail="Analysis failed")

    return {
        "symbol": symbol.upper(),
        "current_price": result.current_price,
        "signal": result.signal.value,
        "conviction": result.conviction.value,
        "composite_score": result.scores.composite_score,
        "trend": result.primary_trend.value,
        "trend_strength": result.trend_strength,
        "weinstein_stage": result.weinstein_stage.value,
        "stage_description": result.stage_description,
        "bullish_factors": result.bullish_factors,
        "bearish_factors": result.bearish_factors,
        "warnings": result.warnings,
        "trade_suggestion": result.trade_suggestion if hasattr(result, 'trade_suggestion') else None,
    }


@router.get("/{symbol}/scores")
async def get_scores(
    symbol: str,
    timeframe: str = Query("1d", description="Data timeframe"),
):
    """Get strategy scores for a stock."""
    result = await analyzer.analyze(symbol.upper(), timeframe)

    if not result:
        raise HTTPException(status_code=404, detail="Analysis failed")

    return {
        "symbol": symbol.upper(),
        "scores": result.scores,
        "signal": result.signal.value,
        "conviction": result.conviction.value,
    }
