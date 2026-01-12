"""
Journal Router
Journal entries for capturing thoughts
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from ..database import get_db
from ..models import JournalEntry
from ..schemas import JournalCreate, JournalResponse

router = APIRouter()


@router.get("/", response_model=dict)
async def list_entries(db: AsyncSession = Depends(get_db)):
    """Get all journal entries"""
    result = await db.execute(
        select(JournalEntry).order_by(JournalEntry.created_at.desc())
    )
    entries = result.scalars().all()
    
    return {
        "success": True,
        "entries": [e.to_dict() for e in entries]
    }


@router.post("/", response_model=dict)
async def create_entry(data: JournalCreate, db: AsyncSession = Depends(get_db)):
    """Create a new journal entry"""
    entry = JournalEntry(
        content=data.content,
        mood=data.mood,
        tags=json.dumps(data.tags) if data.tags else None
    )
    
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    
    return {
        "success": True,
        "entry": entry.to_dict()
    }


@router.get("/{entry_id}", response_model=dict)
async def get_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single journal entry"""
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return {
        "success": True,
        "entry": entry.to_dict()
    }


@router.delete("/{entry_id}", response_model=dict)
async def delete_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a journal entry"""
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    await db.delete(entry)
    
    return {"success": True}


@router.get("/search", response_model=dict)
async def search_entries(q: str, db: AsyncSession = Depends(get_db)):
    """Search journal entries"""
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.content.ilike(f"%{q}%")
        ).order_by(JournalEntry.created_at.desc())
    )
    entries = result.scalars().all()
    
    return {
        "success": True,
        "entries": [e.to_dict() for e in entries]
    }
