"""Notes API routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# In-memory notes storage (in production, use database)
_notes: dict[str, dict] = {}  # symbol -> note


class NoteItem(BaseModel):
    """Stock analysis note model."""
    symbol: str
    company_name: Optional[str] = None
    title: str
    content: str
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime


class NoteCreateRequest(BaseModel):
    """Request to create a note."""
    symbol: str
    title: str
    content: str
    tags: list[str] = []


class NoteUpdateRequest(BaseModel):
    """Request to update a note."""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None


class NotesListResponse(BaseModel):
    """Notes list response model."""
    notes: list[NoteItem]
    count: int
    last_updated: datetime


@router.get("", response_model=NotesListResponse)
async def get_all_notes():
    """Get all notes."""
    items = [
        NoteItem(**note)
        for note in _notes.values()
    ]

    # Sort by updated_at descending
    items.sort(key=lambda x: x.updated_at, reverse=True)

    return NotesListResponse(
        notes=items,
        count=len(items),
        last_updated=datetime.now(),
    )


@router.get("/{symbol}", response_model=NoteItem)
async def get_note(symbol: str):
    """Get note for a specific stock symbol."""
    symbol = symbol.upper()

    if symbol not in _notes:
        raise HTTPException(status_code=404, detail="Note not found for this symbol")

    return NoteItem(**_notes[symbol])


@router.post("", response_model=NoteItem)
async def create_note(request: NoteCreateRequest):
    """Create a new note for a stock."""
    symbol = request.symbol.upper()

    # Check if note already exists
    if symbol in _notes:
        raise HTTPException(
            status_code=409, detail="Note already exists for this symbol. Use PUT to update."
        )

    now = datetime.now()
    note = NoteItem(
        symbol=symbol,
        title=request.title,
        content=request.content,
        tags=request.tags,
        created_at=now,
        updated_at=now,
    )

    _notes[symbol] = note.model_dump()

    return note


@router.put("/{symbol}", response_model=NoteItem)
async def put_note(symbol: str, request: NoteCreateRequest):
    """Create or replace a note for a stock."""
    symbol = symbol.upper()

    now = datetime.now()
    note = NoteItem(
        symbol=symbol,
        title=request.title,
        content=request.content,
        tags=request.tags,
        created_at=_notes[symbol]["created_at"] if symbol in _notes else now,
        updated_at=now,
    )

    _notes[symbol] = note.model_dump()

    return note


@router.patch("/{symbol}", response_model=NoteItem)
async def update_note(symbol: str, request: NoteUpdateRequest):
    """Update partial fields of a note."""
    symbol = symbol.upper()

    if symbol not in _notes:
        raise HTTPException(status_code=404, detail="Note not found for this symbol")

    note = _notes[symbol]

    if request.title is not None:
        note["title"] = request.title
    if request.content is not None:
        note["content"] = request.content
    if request.tags is not None:
        note["tags"] = request.tags

    note["updated_at"] = datetime.now()

    _notes[symbol] = note

    return NoteItem(**note)


@router.delete("/{symbol}")
async def delete_note(symbol: str):
    """Delete a note for a stock."""
    symbol = symbol.upper()

    if symbol not in _notes:
        raise HTTPException(status_code=404, detail="Note not found for this symbol")

    del _notes[symbol]

    return {"message": f"Note for {symbol} deleted"}


@router.post("/clear")
async def clear_all_notes():
    """Clear all notes."""
    global _notes
    count = len(_notes)
    _notes = {}

    return {"message": f"Cleared {count} notes"}
