"""FastAPI application entry point."""

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import stocks, analysis, scanner, watchlist

settings = get_settings()
logger = structlog.get_logger()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Comprehensive stock chart analysis for Indian markets (NSE/BSE)",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["scanner"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("Starting Stock Chart Analyzer", version="1.0.0")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("Shutting down Stock Chart Analyzer")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
