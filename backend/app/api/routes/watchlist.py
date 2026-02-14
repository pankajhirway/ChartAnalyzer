"""Watchlist API routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.yfinance_provider import YFinanceProvider
from app.services.analyzer import AnalyzerService

router = APIRouter()
data_provider = YFinanceProvider()
analyzer = AnalyzerService()

# In-memory watchlist (in production, use database)
_watchlists: dict[str, dict] = {}  # user_id -> watchlist
_default_watchlist: dict[str, dict] = {}  # Global default watchlist


class WatchlistItem(BaseModel):
    """Watchlist item model."""
    symbol: str
    company_name: Optional[str] = None
    added_at: datetime
    notes: Optional[str] = None
    tags: list[str] = []


class WatchlistAddRequest(BaseModel):
    """Request to add item to watchlist."""
    symbol: str
    notes: Optional[str] = None
    tags: list[str] = []


class WatchlistBulkAddRequest(BaseModel):
    """Request to add multiple items to watchlist."""
    symbols: list[str]
    notes: Optional[str] = None
    tags: list[str] = []


class WatchlistBulkAddResponse(BaseModel):
    """Response from bulk add operation."""
    added: list[WatchlistItem]
    count: int


class WatchlistBulkRemoveRequest(BaseModel):
    """Request to remove multiple items from watchlist."""
    symbols: list[str]


class WatchlistResponse(BaseModel):
    """Watchlist response model."""
    items: list[WatchlistItem]
    count: int
    last_updated: datetime


@router.get("", response_model=WatchlistResponse)
async def get_watchlist():
    """Get the current watchlist."""
    items = [
        WatchlistItem(**item)
        for item in _default_watchlist.values()
    ]

    # Sort by added_at descending
    items.sort(key=lambda x: x.added_at, reverse=True)

    return WatchlistResponse(
        items=items,
        count=len(items),
        last_updated=datetime.now(),
    )


@router.post("", response_model=WatchlistItem)
async def add_to_watchlist(request: WatchlistAddRequest):
    """Add a stock to the watchlist."""
    symbol = request.symbol.upper()

    # Verify stock exists
    stock_info = await data_provider.get_stock_info(symbol)
    if not stock_info:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Add to watchlist
    item = WatchlistItem(
        symbol=symbol,
        company_name=stock_info.company_name,
        added_at=datetime.now(),
        notes=request.notes,
        tags=request.tags,
    )

    _default_watchlist[symbol] = item.model_dump()

    return item


@router.delete("/{symbol}")
async def remove_from_watchlist(symbol: str):
    """Remove a stock from the watchlist."""
    symbol = symbol.upper()

    if symbol not in _default_watchlist:
        raise HTTPException(status_code=404, detail="Stock not in watchlist")

    del _default_watchlist[symbol]

    return {"message": f"{symbol} removed from watchlist"}


@router.get("/quotes")
async def get_watchlist_quotes():
    """Get current quotes for all watchlist items."""
    if not _default_watchlist:
        return {"quotes": {}, "count": 0}

    symbols = list(_default_watchlist.keys())
    quotes = await data_provider.get_multiple_quotes(symbols)

    return {
        "quotes": quotes,
        "count": len(quotes),
    }


@router.get("/analysis")
async def analyze_watchlist():
    """Run quick analysis on all watchlist items."""
    if not _default_watchlist:
        return {"results": [], "count": 0}

    results = []
    symbols = list(_default_watchlist.keys())

    for symbol in symbols:
        try:
            analysis = await analyzer.analyze(symbol)
            if analysis:
                results.append({
                    "symbol": symbol,
                    "current_price": analysis.current_price,
                    "signal": analysis.signal.value,
                    "conviction": analysis.conviction.value,
                    "composite_score": analysis.scores.composite_score,
                    "trend": analysis.primary_trend.value,
                    "weinstein_stage": analysis.weinstein_stage.value,
                    "patterns": [p.pattern_name for p in analysis.detected_patterns[:3]],
                })
        except Exception:
            pass

    # Sort by composite score
    results.sort(key=lambda x: x["composite_score"], reverse=True)

    return {
        "results": results,
        "count": len(results),
    }


@router.post("/bulk-add", response_model=WatchlistBulkAddResponse)
async def bulk_add_to_watchlist(request: WatchlistBulkAddRequest):
    """Add multiple stocks to the watchlist."""
    if len(request.symbols) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 symbols at a time")

    added_items = []

    for symbol in request.symbols:
        symbol = symbol.upper()

        # Skip if already in watchlist
        if symbol in _default_watchlist:
            continue

        # Verify stock exists
        stock_info = await data_provider.get_stock_info(symbol)
        if not stock_info:
            continue

        # Add to watchlist
        item = WatchlistItem(
            symbol=symbol,
            company_name=stock_info.company_name,
            added_at=datetime.now(),
            notes=request.notes,
            tags=request.tags,
        )

        _default_watchlist[symbol] = item.model_dump()
        added_items.append(item)

    return WatchlistBulkAddResponse(added=added_items, count=len(added_items))


@router.patch("/{symbol}")
async def update_watchlist_item(
    symbol: str,
    notes: Optional[str] = None,
    tags: Optional[list[str]] = None,
):
    """Update notes or tags for a watchlist item."""
    symbol = symbol.upper()

    if symbol not in _default_watchlist:
        raise HTTPException(status_code=404, detail="Stock not in watchlist")

    item = _default_watchlist[symbol]

    if notes is not None:
        item["notes"] = notes
    if tags is not None:
        item["tags"] = tags

    _default_watchlist[symbol] = item

    return WatchlistItem(**item)


@router.post("/bulk-remove")
async def bulk_remove_from_watchlist(request: WatchlistBulkRemoveRequest):
    """Remove multiple stocks from the watchlist."""
    if len(request.symbols) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 symbols at a time")

    removed_symbols = []

    for symbol in request.symbols:
        symbol = symbol.upper()

        if symbol in _default_watchlist:
            del _default_watchlist[symbol]
            removed_symbols.append(symbol)

    return {
        "removed": removed_symbols,
        "count": len(removed_symbols),
    }


@router.post("/clear")
async def clear_watchlist():
    """Clear all items from the watchlist."""
    global _default_watchlist
    count = len(_default_watchlist)
    _default_watchlist = {}

    return {"message": f"Cleared {count} items from watchlist"}
