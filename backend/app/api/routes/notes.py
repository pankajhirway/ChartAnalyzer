"""Notes API routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.annotation import (
    AnalysisNoteCreate,
    AnalysisNoteDB,
    AnalysisNoteListResponse,
    AnalysisNoteResponse,
    AnalysisNoteUpdate,
)

router = APIRouter()


@router.get("", response_model=AnalysisNoteListResponse)
async def get_all_notes(
    db: AsyncSession = Depends(get_db_session),
):
    """Get all analysis notes."""
    result = await db.execute(
        select(AnalysisNoteDB)
        .order_by(AnalysisNoteDB.updated_at.desc())
    )
    notes = result.scalars().all()

    return AnalysisNoteListResponse(
        symbol="all",
        count=len(notes),
        notes=[
            AnalysisNoteResponse.model_validate(note) for note in notes
        ],
    )


@router.get("/{symbol}", response_model=AnalysisNoteResponse)
async def get_note(
    symbol: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Get note for a specific stock symbol."""
    symbol = symbol.upper()

    result = await db.execute(
        select(AnalysisNoteDB).where(AnalysisNoteDB.symbol == symbol)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found for this symbol")

    return AnalysisNoteResponse.model_validate(note)


@router.post("", response_model=AnalysisNoteResponse)
async def create_note(
    request: AnalysisNoteCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new note for a stock."""
    symbol = request.symbol.upper()

    # Check if note already exists
    result = await db.execute(
        select(AnalysisNoteDB).where(AnalysisNoteDB.symbol == symbol)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409, detail="Note already exists for this symbol. Use PUT to update."
        )

    # Create new note
    note = AnalysisNoteDB(
        symbol=symbol,
        title=request.title,
        content=request.content,
        tags=request.tags,
        category=request.category,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(note)
    await db.commit()
    await db.refresh(note)

    return AnalysisNoteResponse.model_validate(note)


@router.put("/{symbol}", response_model=AnalysisNoteResponse)
async def put_note(
    symbol: str,
    request: AnalysisNoteCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Create or replace a note for a stock."""
    symbol = symbol.upper()

    # Check if note exists
    result = await db.execute(
        select(AnalysisNoteDB).where(AnalysisNoteDB.symbol == symbol)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing note
        await db.execute(
            update(AnalysisNoteDB)
            .where(AnalysisNoteDB.symbol == symbol)
            .values(
                title=request.title,
                content=request.content,
                tags=request.tags,
                category=request.category,
                updated_at=datetime.utcnow(),
            )
        )
        await db.commit()

        # Get updated note
        result = await db.execute(
            select(AnalysisNoteDB).where(AnalysisNoteDB.symbol == symbol)
        )
        note = result.scalar_one()
    else:
        # Create new note
        note = AnalysisNoteDB(
            symbol=symbol,
            title=request.title,
            content=request.content,
            tags=request.tags,
            category=request.category,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)

    return AnalysisNoteResponse.model_validate(note)


@router.patch("/{symbol}", response_model=AnalysisNoteResponse)
async def update_note(
    symbol: str,
    request: AnalysisNoteUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """Update partial fields of a note."""
    symbol = symbol.upper()

    # Check if note exists
    result = await db.execute(
        select(AnalysisNoteDB).where(AnalysisNoteDB.symbol == symbol)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found for this symbol")

    # Build update data
    update_data = {"updated_at": datetime.utcnow()}

    if request.title is not None:
        update_data["title"] = request.title
    if request.content is not None:
        update_data["content"] = request.content
    if request.tags is not None:
        update_data["tags"] = request.tags
    if request.category is not None:
        update_data["category"] = request.category

    # Perform update
    await db.execute(
        update(AnalysisNoteDB)
        .where(AnalysisNoteDB.symbol == symbol)
        .values(**update_data)
    )
    await db.commit()

    # Get updated note
    result = await db.execute(
        select(AnalysisNoteDB).where(AnalysisNoteDB.symbol == symbol)
    )
    updated_note = result.scalar_one()

    return AnalysisNoteResponse.model_validate(updated_note)


@router.delete("/{symbol}")
async def delete_note(
    symbol: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a note for a stock."""
    symbol = symbol.upper()

    # Check if note exists
    result = await db.execute(
        select(AnalysisNoteDB).where(AnalysisNoteDB.symbol == symbol)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found for this symbol")

    # Delete note
    await db.execute(
        delete(AnalysisNoteDB).where(AnalysisNoteDB.symbol == symbol)
    )
    await db.commit()

    return {"message": f"Note for {symbol} deleted"}


@router.post("/clear")
async def clear_all_notes(
    db: AsyncSession = Depends(get_db_session),
):
    """Clear all notes."""
    # Get count first
    result = await db.execute(select(AnalysisNoteDB))
    notes = result.scalars().all()
    count = len(notes)

    # Delete all
    await db.execute(delete(AnalysisNoteDB))
    await db.commit()

    return {"message": f"Cleared {count} notes"}
