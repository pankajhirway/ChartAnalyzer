"""Annotations API routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.annotation import (
    AnnotationCreate,
    AnnotationDB,
    AnnotationListResponse,
    AnnotationResponse,
    AnnotationUpdate,
)

router = APIRouter()


@router.get("/{symbol}", response_model=AnnotationListResponse)
async def get_annotations(
    symbol: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Get all annotations for a stock symbol."""
    symbol = symbol.upper()

    result = await db.execute(
        select(AnnotationDB)
        .where(AnnotationDB.symbol == symbol)
        .order_by(AnnotationDB.created_at.desc())
    )
    annotations = result.scalars().all()

    return AnnotationListResponse(
        symbol=symbol,
        count=len(annotations),
        annotations=[
            AnnotationResponse.model_validate(annotation) for annotation in annotations
        ],
    )


@router.post("", response_model=AnnotationResponse)
async def create_annotation(
    request: AnnotationCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new annotation."""
    symbol = request.symbol.upper()

    # Create new annotation
    annotation = AnnotationDB(
        symbol=symbol,
        annotation_type=request.annotation_type.value,
        title=request.title,
        notes=request.notes,
        x1=request.x1,
        y1=request.y1,
        x2=request.x2,
        y2=request.y2,
        color=request.color.value,
        line_style=request.line_style.value,
        line_width=request.line_width.value,
        visible=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)

    return AnnotationResponse.model_validate(annotation)


@router.get("/id/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Get a specific annotation by ID."""
    result = await db.execute(
        select(AnnotationDB).where(AnnotationDB.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    return AnnotationResponse.model_validate(annotation)


@router.patch("/id/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: int,
    request: AnnotationUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """Update an annotation."""
    # Check if annotation exists
    result = await db.execute(
        select(AnnotationDB).where(AnnotationDB.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    # Build update data
    update_data = {"updated_at": datetime.utcnow()}

    if request.title is not None:
        update_data["title"] = request.title
    if request.notes is not None:
        update_data["notes"] = request.notes
    if request.x1 is not None:
        update_data["x1"] = request.x1
    if request.y1 is not None:
        update_data["y1"] = request.y1
    if request.x2 is not None:
        update_data["x2"] = request.x2
    if request.y2 is not None:
        update_data["y2"] = request.y2
    if request.color is not None:
        update_data["color"] = request.color.value
    if request.line_style is not None:
        update_data["line_style"] = request.line_style.value
    if request.line_width is not None:
        update_data["line_width"] = request.line_width.value
    if request.visible is not None:
        update_data["visible"] = request.visible

    # Perform update
    await db.execute(
        update(AnnotationDB)
        .where(AnnotationDB.id == annotation_id)
        .values(**update_data)
    )
    await db.commit()

    # Get updated annotation
    result = await db.execute(
        select(AnnotationDB).where(AnnotationDB.id == annotation_id)
    )
    updated_annotation = result.scalar_one()

    return AnnotationResponse.model_validate(updated_annotation)


@router.delete("/id/{annotation_id}")
async def delete_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Delete an annotation."""
    # Check if annotation exists
    result = await db.execute(
        select(AnnotationDB).where(AnnotationDB.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    # Delete annotation
    await db.execute(
        delete(AnnotationDB).where(AnnotationDB.id == annotation_id)
    )
    await db.commit()

    return {"message": f"Annotation {annotation_id} deleted"}


@router.delete("/{symbol}/all")
async def delete_all_annotations(
    symbol: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Delete all annotations for a symbol."""
    symbol = symbol.upper()

    # Check if any annotations exist
    result = await db.execute(
        select(AnnotationDB).where(AnnotationDB.symbol == symbol)
    )
    annotations = result.scalars().all()

    if not annotations:
        raise HTTPException(status_code=404, detail="No annotations found for symbol")

    count = len(annotations)

    # Delete all annotations for symbol
    await db.execute(
        delete(AnnotationDB).where(AnnotationDB.symbol == symbol)
    )
    await db.commit()

    return {"message": f"Deleted {count} annotations for {symbol}"}
