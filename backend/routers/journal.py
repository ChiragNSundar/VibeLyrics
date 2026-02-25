"""
Journal Router
- Create and list journal entries
- Semantic search using vector embeddings
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
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


class JournalSearchRequest(BaseModel):
    query: str
    mode: str = "auto"  # "semantic", "keyword", or "auto"
    top_k: int = 5


@router.post("", response_model=dict)
async def create_entry(entry: JournalCreate, db: AsyncSession = Depends(get_db)):
    """Create a new journal entry and index it for semantic search"""
    import json
    new_entry = JournalEntry(
        content=entry.content,
        mood=entry.mood,
        tags=json.dumps(entry.tags)
    )
    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)
    
    # Index in vector store for semantic search
    try:
        from ..services.vector_search import get_vector_store
        vector_store = get_vector_store()
        vector_store.add_entry(new_entry.id, new_entry.content)
    except Exception as e:
        print(f"[Journal] Vector indexing failed (non-fatal): {e}")
    
    return {"success": True, "entry": new_entry.to_dict()}


@router.get("", response_model=dict)
async def get_entries(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """List journal entries"""
    result = await db.execute(
        select(JournalEntry).order_by(desc(JournalEntry.created_at)).limit(limit)
    )
    entries = result.scalars().all()
    return {"success": True, "entries": [e.to_dict() for e in entries]}


@router.get("/search", response_model=dict)
async def search_journal(
    q: str,
    mode: str = "auto",
    top_k: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """
    Search journal entries using semantic or keyword search.
    
    - mode=semantic: Uses sentence-transformers for meaning-based search
    - mode=keyword: Uses simple word overlap matching
    - mode=auto: Uses semantic if available, falls back to keyword
    """
    try:
        from ..services.vector_search import get_vector_store
        vector_store = get_vector_store()
        
        # Ensure all entries are indexed
        result = await db.execute(
            select(JournalEntry).order_by(desc(JournalEntry.created_at))
        )
        entries = result.scalars().all()
        
        # Quick check: if store is empty but DB has entries, reindex
        if entries and not vector_store._entries:
            vector_store.reindex_all([
                {"id": e.id, "content": e.content} for e in entries
            ])
        
        results = vector_store.search(q, top_k=top_k, mode=mode)
        
        # Enrich results with full entry data from DB
        enriched = []
        for r in results:
            entry = await db.get(JournalEntry, r["entry_id"])
            if entry:
                enriched.append({
                    **r,
                    "mood": entry.mood,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "content": entry.content  # Use full content from DB
                })
            else:
                enriched.append(r)
        
        return {
            "success": True,
            "query": q,
            "mode": mode,
            "results": enriched,
            "total": len(enriched)
        }
        
    except Exception as e:
        print(f"[Journal] Search error: {e}")
        # Fallback to basic DB search
        result = await db.execute(
            select(JournalEntry)
            .where(JournalEntry.content.contains(q))
            .order_by(desc(JournalEntry.created_at))
            .limit(top_k)
        )
        entries = result.scalars().all()
        
        return {
            "success": True,
            "query": q,
            "mode": "fallback",
            "results": [
                {
                    "entry_id": e.id,
                    "content": e.content,
                    "mood": e.mood,
                    "similarity": 1.0,
                    "match_type": "contains",
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in entries
            ],
            "total": len(entries)
        }


@router.post("/reindex", response_model=dict)
async def reindex_journal(db: AsyncSession = Depends(get_db)):
    """Reindex all journal entries in the vector store"""
    try:
        from ..services.vector_search import get_vector_store
        vector_store = get_vector_store()
        
        result = await db.execute(
            select(JournalEntry).order_by(JournalEntry.created_at)
        )
        entries = result.scalars().all()
        
        count = vector_store.reindex_all([
            {"id": e.id, "content": e.content} for e in entries
        ])
        
        return {
            "success": True,
            "message": f"Reindexed {count} entries",
            "total": count,
            "mode": "semantic" if vector_store.is_available else "keyword"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

