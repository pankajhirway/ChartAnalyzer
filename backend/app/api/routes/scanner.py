"""Market scanner API routes."""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.scanner import ScannerService, ScanFilter, ScanResult, ScanProgress
from app.utils.constants import INDEX_CONSTITUENTS

router = APIRouter()
scanner = ScannerService()


class ScanRequest(BaseModel):
    """Request body for scan."""
    universe: str = "nifty50"
    min_composite_score: float = 50.0
    max_composite_score: float = 100.0
    signal: Optional[str] = None
    min_conviction: Optional[str] = None
    trend: Optional[str] = None
    weinstein_stage: Optional[int] = None
    max_results: int = 20


@router.post("/run", response_model=list[ScanResult])
async def run_scan(request: ScanRequest):
    """Run a market scan with custom filters.

    Scans the specified universe of stocks and returns those
    matching the filter criteria.
    """
    scan_filter = ScanFilter(
        min_composite_score=request.min_composite_score,
        max_composite_score=request.max_composite_score,
        signal=request.signal,
        min_conviction=request.min_conviction,
        trend=request.trend,
        weinstein_stage=request.weinstein_stage,
    )

    results = await scanner.scan_universe(
        universe=request.universe,
        scan_filter=scan_filter,
        max_results=request.max_results,
    )

    return results


@router.get("/presets")
async def get_scan_presets():
    """Get available preset scan configurations with full definitions.

    Returns preset configurations including:
    - id: Unique preset identifier
    - name: Display name
    - description: What the preset scans for
    - strategy_rationale: Why this strategy works
    - filter: Filter criteria for the scan
    - recommended_universe: Recommended stock universe
    - holding_period: Recommended holding period
    - difficulty: Difficulty level (beginner/intermediate/advanced)
    """
    return scanner.get_preset_filters()


@router.get("/breakouts")
async def scan_breakouts(
    universe: str = Query("nifty50", description="Universe to scan"),
    min_volume_ratio: float = Query(1.5, description="Minimum volume ratio"),
):
    """Scan for breakout stocks.

    Returns stocks that are breaking out with volume confirmation.
    """
    results = await scanner.scan_for_breakouts(
        universe=universe,
        min_volume_ratio=min_volume_ratio,
    )
    return results


@router.get("/stage2")
async def scan_stage2(
    universe: str = Query("nifty200", description="Universe to scan"),
):
    """Scan for Weinstein Stage 2 stocks.

    Returns stocks that are in the advancing Stage 2 phase.
    """
    results = await scanner.scan_stage2_stocks(universe=universe)
    return results


@router.get("/vcp-setups")
async def scan_vcp(
    universe: str = Query("nifty200", description="Universe to scan"),
):
    """Scan for Minervini VCP setups.

    Returns stocks showing Volatility Contraction Pattern formations.
    """
    results = await scanner.scan_minervini_setups(universe=universe)
    return results


@router.get("/progress/{scan_id}", response_model=ScanProgress)
async def get_scan_progress(scan_id: str):
    """Get the progress of a scan operation.

    Returns the current status and progress of a scan identified by its ID.
    If the scan ID is not found, returns a 404 error.
    """
    progress = scanner.get_scan_progress(scan_id)

    if progress is None:
        raise HTTPException(status_code=404, detail=f"Scan ID '{scan_id}' not found")

    return progress


@router.get("/universes")
async def get_available_universes():
    """Get list of available scanning universes."""
    return {
        "universes": [
            {
                "id": "nifty50", 
                "name": "Nifty 50", 
                "count": len(INDEX_CONSTITUENTS["nifty50"]), 
                "description": "Top 50 large cap stocks"
            },
            {
                "id": "nifty100", 
                "name": "Nifty 100", 
                "count": len(INDEX_CONSTITUENTS["nifty100"]), 
                "description": "Top 100 stocks by market cap"
            },
            {
                "id": "nifty200", 
                "name": "Nifty 200", 
                "count": len(INDEX_CONSTITUENTS["nifty200"]), 
                "description": "Top 200 stocks by market cap"
            },
            {
                "id": "nifty500", 
                "name": "Nifty 500", 
                "count": len(INDEX_CONSTITUENTS["nifty500"]), 
                "description": "Broad market index (approx. 500)"
            },
            {
                "id": "fnO", 
                "name": "F&O Stocks", 
                "count": len(INDEX_CONSTITUENTS["fnO"]), 
                "description": "Futures & Options segment"
            },
        ]
    }
