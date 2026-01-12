from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import List
from ..database import get_db
from ..models import JournalEntry
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class JournalCreate(BaseModel):
    content: str
    mood: str = "Neutral"
    tags: List[str] = []

class JournalResponse(BaseModel):
    id: int
    content: str
    mood: str
    created_at: str

@router.post("/journal", response_model=dict)
async def create_entry(entry: JournalCreate, db: Session = Depends(get_db)):
    import json
    new_entry = JournalEntry(
        content=entry.content,
        mood=entry.mood,
        tags=json.dumps(entry.tags)
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {"success": True, "entry": new_entry.to_dict()}

@router.get("/journal", response_model=dict)
async def get_entries(limit: int = 10, db: Session = Depends(get_db)):
    entries = db.scalars(
        select(JournalEntry).order_by(desc(JournalEntry.created_at)).limit(limit)
    ).all()
    return {"success": True, "entries": [e.to_dict() for e in entries]}
