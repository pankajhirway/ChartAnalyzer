"""Stock data API routes."""

from fastapi import APIRouter, HTTPException, Query

from app.core.yfinance_provider import YFinanceProvider
from app.models.stock import Stock, StockQuote, StockSearchResult, PriceDataResponse
from app.models.fundamental import FundamentalData, FundamentalScore
from app.services.fundamental_scorer import FundamentalScorer

router = APIRouter()
data_provider = YFinanceProvider()
scorer = FundamentalScorer()


@router.get("/search", response_model=list[StockSearchResult])
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """Search for stocks by symbol or company name."""
    results = await data_provider.search_stocks(q, limit)
    return results


@router.get("/{symbol}", response_model=Stock)
async def get_stock(symbol: str):
    """Get stock information."""
    stock = await data_provider.get_stock_info(symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@router.get("/{symbol}/quote", response_model=StockQuote)
async def get_stock_quote(symbol: str):
    """Get current quote for a stock."""
    quote = await data_provider.get_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not available")
    return quote


@router.get("/{symbol}/history", response_model=PriceDataResponse)
async def get_stock_history(
    symbol: str,
    timeframe: str = Query("1d", description="Data timeframe (1d, 1h, 1w, etc.)"),
    days: int = Query(365, ge=30, le=730, description="Number of days of history"),
):
    """Get historical price data for a stock."""
    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    data = await data_provider.get_historical_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timeframe=timeframe,
    )

    if not data:
        raise HTTPException(status_code=404, detail="Historical data not available")

    return PriceDataResponse(
        symbol=symbol.upper(),
        timeframe=timeframe,
        data=data,
    )


@router.post("/quotes/batch", response_model=dict[str, StockQuote])
async def get_batch_quotes(symbols: list[str]):
    """Get quotes for multiple stocks."""
    if len(symbols) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 symbols at a time")

    quotes = await data_provider.get_multiple_quotes(symbols)
    return quotes


@router.get("/{symbol}/fundamentals", response_model=FundamentalData)
async def get_stock_fundamentals(symbol: str):
    """Get fundamental metrics for a stock."""
    fundamentals = await data_provider.get_fundamentals(symbol)
    if not fundamentals:
        raise HTTPException(status_code=404, detail="Fundamental data not available")
    return fundamentals


@router.post("/{symbol}/fundamentals/refresh", response_model=FundamentalData)
async def refresh_stock_fundamentals(symbol: str):
    """Force refresh fundamental metrics from source."""
    fundamentals = await data_provider.refresh_fundamentals(symbol)
    if not fundamentals:
        raise HTTPException(status_code=404, detail="Fundamental data not available")
    return fundamentals


@router.get("/{symbol}/fundamentals/score", response_model=FundamentalScore)
async def get_stock_fundamental_score(symbol: str):
    """Get fundamental score for a stock."""
    fundamentals = await data_provider.get_fundamentals(symbol)
    if not fundamentals:
        raise HTTPException(status_code=404, detail="Fundamental data not available")

    score = scorer.score(fundamentals)
    if not score:
        raise HTTPException(status_code=404, detail="Insufficient data for scoring")
    return score
