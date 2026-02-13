"""Annotation and analysis note models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""

    pass


# =============================================================================
# Enums
# =============================================================================

class AnnotationType(str, Enum):
    """Annotation type enumeration."""
    TRENDLINE = "TRENDLINE"
    HORIZONTAL_LINE = "HORIZONTAL_LINE"
    RECTANGLE = "RECTANGLE"
    TEXT = "TEXT"
    ARROW = "ARROW"
    FIBONACCI = "FIBONACCI"
    SUPPORT_RESISTANCE = "SUPPORT_RESISTANCE"


class Color(str, Enum):
    """Color enumeration for annotations."""
    RED = "#FF0000"
    GREEN = "#00FF00"
    BLUE = "#0000FF"
    YELLOW = "#FFFF00"
    ORANGE = "#FFA500"
    PURPLE = "#800080"
    CYAN = "#00FFFF"
    MAGENTA = "#FF00FF"
    WHITE = "#FFFFFF"
    BLACK = "#000000"


class LineStyle(str, Enum):
    """Line style enumeration."""
    SOLID = "SOLID"
    DASHED = "DASHED"
    DOTTED = "DOTTED"


class LineWidth(str, Enum):
    """Line width enumeration."""
    THIN = "1"
    NORMAL = "2"
    THICK = "3"
    VERY_THICK = "4"


# =============================================================================
# SQLAlchemy ORM Models
# =============================================================================

class AnnotationDB(Base):
    """SQLAlchemy ORM model for annotations.

    Represents a chart annotation (trendline, horizontal line, etc.)
    that persists across sessions.
    """
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    # Annotation details
    annotation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Coordinates and appearance
    x1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Start x (timestamp)
    y1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Start y (price)
    x2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # End x (timestamp)
    y2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # End y (price)
    color: Mapped[str] = mapped_column(String(20), default=Color.BLUE, nullable=False)
    line_style: Mapped[str] = mapped_column(String(20), default=LineStyle.SOLID, nullable=False)
    line_width: Mapped[str] = mapped_column(String(10), default=LineWidth.NORMAL, nullable=False)

    # Visibility
    visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<AnnotationDB(id={self.id}, symbol={self.symbol}, "
            f"type={self.annotation_type})>"
        )


class AnalysisNoteDB(Base):
    """SQLAlchemy ORM model for analysis notes.

    Represents user notes and commentary for a specific stock.
    """
    __tablename__ = "analysis_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    # Note content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Comma-separated tags

    # Categorization
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )  # e.g., "Trade Rationale", "Pattern Analysis", "Risk Assessment"

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<AnalysisNoteDB(id={self.id}, symbol={self.symbol}, "
            f"title={self.title})>"
        )


# =============================================================================
# Pydantic Models for API
# =============================================================================

# ----- Request Models -----

class AnnotationCreate(BaseModel):
    """Request model for creating an annotation."""
    symbol: str = Field(..., description="Stock symbol")
    annotation_type: AnnotationType = Field(..., description="Type of annotation")
    title: Optional[str] = Field(None, description="Annotation title")
    notes: Optional[str] = Field(None, description="Annotation notes")
    x1: Optional[float] = Field(None, description="Start x coordinate (timestamp)")
    y1: Optional[float] = Field(None, description="Start y coordinate (price)")
    x2: Optional[float] = Field(None, description="End x coordinate (timestamp)")
    y2: Optional[float] = Field(None, description="End y coordinate (price)")
    color: Color = Field(default=Color.BLUE, description="Annotation color")
    line_style: LineStyle = Field(default=LineStyle.SOLID, description="Line style")
    line_width: LineWidth = Field(default=LineWidth.NORMAL, description="Line width")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "annotation_type": "TRENDLINE",
                "title": "Uptrend support",
                "notes": "Strong support line, tested 3 times",
                "x1": 1705305600000,
                "y1": 2400.0,
                "x2": 1707897600000,
                "y2": 2450.0,
                "color": "#00FF00",
                "line_style": "SOLID",
                "line_width": "2"
            }
        }


class AnnotationUpdate(BaseModel):
    """Request model for updating an annotation."""
    title: Optional[str] = Field(None, description="Annotation title")
    notes: Optional[str] = Field(None, description="Annotation notes")
    x1: Optional[float] = Field(None, description="Start x coordinate (timestamp)")
    y1: Optional[float] = Field(None, description="Start y coordinate (price)")
    x2: Optional[float] = Field(None, description="End x coordinate (timestamp)")
    y2: Optional[float] = Field(None, description="End y coordinate (price)")
    color: Optional[Color] = Field(None, description="Annotation color")
    line_style: Optional[LineStyle] = Field(None, description="Line style")
    line_width: Optional[LineWidth] = Field(None, description="Line width")
    visible: Optional[bool] = Field(None, description="Visibility status")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated trendline",
                "y2": 2460.0,
                "visible": True
            }
        }


class AnalysisNoteCreate(BaseModel):
    """Request model for creating an analysis note."""
    symbol: str = Field(..., description="Stock symbol")
    title: str = Field(..., description="Note title", min_length=1, max_length=200)
    content: str = Field(..., description="Note content", min_length=1)
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    category: Optional[str] = Field(None, description="Note category")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "title": "VCP Setup Analysis",
                "content": "Forming a nice VCP pattern with 3 contractions. "
                          "Volume drying up on pullbacks. Waiting for breakout "
                          "above 2500 with volume expansion.",
                "tags": "VCP, breakout, bullish",
                "category": "Pattern Analysis"
            }
        }


class AnalysisNoteUpdate(BaseModel):
    """Request model for updating an analysis note."""
    title: Optional[str] = Field(None, description="Note title", min_length=1, max_length=200)
    content: Optional[str] = Field(None, description="Note content", min_length=1)
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    category: Optional[str] = Field(None, description="Note category")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Updated analysis content here...",
                "tags": "VCP, breakout, bullish, updated"
            }
        }


# ----- Response Models -----

class AnnotationResponse(BaseModel):
    """Response model for an annotation."""
    id: int
    symbol: str
    annotation_type: AnnotationType
    title: Optional[str] = None
    notes: Optional[str] = None
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None
    color: str
    line_style: str
    line_width: str
    visible: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "symbol": "RELIANCE",
                "annotation_type": "TRENDLINE",
                "title": "Uptrend support",
                "notes": "Strong support line",
                "x1": 1705305600000,
                "y1": 2400.0,
                "x2": 1707897600000,
                "y2": 2450.0,
                "color": "#00FF00",
                "line_style": "SOLID",
                "line_width": "2",
                "visible": True,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }


class AnalysisNoteResponse(BaseModel):
    """Response model for an analysis note."""
    id: int
    symbol: str
    title: str
    content: str
    tags: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "symbol": "RELIANCE",
                "title": "VCP Setup Analysis",
                "content": "Forming a nice VCP pattern with 3 contractions.",
                "tags": "VCP, breakout, bullish",
                "category": "Pattern Analysis",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }


class AnnotationListResponse(BaseModel):
    """Response model for a list of annotations."""
    symbol: str
    count: int
    annotations: list[AnnotationResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "count": 3,
                "annotations": []
            }
        }


class AnalysisNoteListResponse(BaseModel):
    """Response model for a list of analysis notes."""
    symbol: str
    count: int
    notes: list[AnalysisNoteResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "count": 2,
                "notes": []
            }
        }


# Export both the ORM base and the Pydantic models
__all__ = [
    # SQLAlchemy ORM
    "Base",
    "AnnotationDB",
    "AnalysisNoteDB",
    # Enums
    "AnnotationType",
    "Color",
    "LineStyle",
    "LineWidth",
    # Pydantic Request Models
    "AnnotationCreate",
    "AnnotationUpdate",
    "AnalysisNoteCreate",
    "AnalysisNoteUpdate",
    # Pydantic Response Models
    "AnnotationResponse",
    "AnalysisNoteResponse",
    "AnnotationListResponse",
    "AnalysisNoteListResponse",
]

# Aliases for simpler imports (matching verification expectations)
Annotation = AnnotationDB
AnalysisNote = AnalysisNoteDB
