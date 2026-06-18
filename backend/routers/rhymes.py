"""
Rhymes Router
Rhyme lookups, thesaurus, and multi-syllable rhymes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from ..schemas import RhymeLookup, ThesaurusLookup, RhymeExtract, PhoneticRegister
from ..services.rhyme_detector import RhymeDetector
from ..database import get_db

router = APIRouter()
_rhyme_detector = RhymeDetector()


@router.post("/rhymes/lookup", response_model=dict)
async def lookup_rhymes(data: RhymeLookup):
    """Look up rhymes for a word"""
    rhymes = _rhyme_detector.find_rhymes(data.word, max_results=data.max_results)
    
    return {
        "success": True,
        "word": data.word,
        "rhymes": rhymes
    }


@router.get("/rhymes/{word}", response_model=dict)
async def get_rhymes(word: str, limit: int = 20):
    """Get rhymes for a word (simple endpoint)"""
    rhymes = _rhyme_detector.find_rhymes(word, max_results=limit)
    
    return {
        "success": True,
        "word": word,
        "rhymes": rhymes
    }


@router.get("/rhymes/{word}/multi", response_model=dict)
async def get_multi_rhymes(word: str):
    """Get multi-syllable rhymes"""
    multi_rhymes = _rhyme_detector.find_multi_syllable_rhymes(word)
    
    return {
        "success": True,
        "word": word,
        "multi_rhymes": multi_rhymes
    }


@router.post("/thesaurus/lookup", response_model=dict)
async def thesaurus_lookup(data: ThesaurusLookup):
    """Combined rhyme and synonym lookup"""
    result = {
        "success": True,
        "word": data.word
    }
    
    if data.include_rhymes:
        result["rhymes"] = _rhyme_detector.find_rhymes(data.word)
    
    if data.include_synonyms:
        result["synonyms"] = _rhyme_detector.get_synonyms(data.word)
    
    return result


@router.get("/slang/{category}", response_model=dict)
async def get_slang(category: str):
    """Get hip-hop slang for a category"""
    slang = _rhyme_detector.get_slang_by_category(category)
    
    return {
        "success": True,
        "category": category,
        "slang": slang
    }


@router.get("/slang", response_model=dict)
async def get_slang_categories():
    """Get all slang categories"""
    categories = _rhyme_detector.get_slang_categories()
    
    return {
        "success": True,
        "categories": categories
    }


class DoppelreimLookup(BaseModel):
    word: str
    language: str = "en"
    mode: str = "vowel"
    allow_slang: bool = True
    max_results: int = 30


class RhymeVoteSchema(BaseModel):
    source_word: str
    target_word: str
    is_valid_rhyme: bool


@router.post("/rhymes/doppelreim", response_model=dict)
async def lookup_doppelreim(data: DoppelreimLookup, db: AsyncSession = Depends(get_db)):
    """Advanced multisyllabic lookup (Classic, Slant, Multi-word)"""
    results = await _rhyme_detector.find_doppelreim_rhymes(
        db, data.word, data.language, data.mode, data.allow_slang, data.max_results
    )
    return {
        "success": True,
        "results": results
    }


@router.post("/rhymes/vote", response_model=dict)
async def vote_rhyme(data: RhymeVoteSchema, db: AsyncSession = Depends(get_db)):
    """Submit community voting feedback to rank rhymes"""
    from ..models import RhymeFeedback, MultisyllabicWord
    
    query = select(RhymeFeedback).where(
        func.lower(RhymeFeedback.source_word) == data.source_word.lower(),
        func.lower(RhymeFeedback.target_word) == data.target_word.lower()
    )
    res = await db.execute(query)
    fb = res.scalar()
    
    if fb:
        fb.votes_count += 1
        fb.is_valid_rhyme = data.is_valid_rhyme
    else:
        fb = RhymeFeedback(
            source_word=data.source_word,
            target_word=data.target_word,
            is_valid_rhyme=data.is_valid_rhyme,
            votes_count=1
        )
        db.add(fb)
        
    diff = 1 if data.is_valid_rhyme else -1
    up_query = select(MultisyllabicWord).where(
        func.lower(MultisyllabicWord.word) == data.target_word.lower()
    )
    res_w = await db.execute(up_query)
    words = res_w.scalars().all()
    for w in words:
        w.upvotes = max(0, w.upvotes + diff)
        
    try:
        await db.commit()
        _rhyme_detector.clear_cache()
        return {"success": True, "message": "Vote recorded successfully."}
    except Exception as e:
        await db.rollback()
        return {"success": False, "error": str(e)}


@router.post("/rhymes/extract", response_model=dict)
async def extract_word_phonetics(data: RhymeExtract):
    """Run phonetic vowel extraction on a word (English, Hindi, or Kannada)"""
    vowel_seq, exact_key, syllable_count = _rhyme_detector.extract_vowels(
        data.word, data.language
    )
    return {
        "success": True,
        "word": data.word,
        "vowel_sequence": vowel_seq,
        "exact_key": exact_key,
        "syllable_count": syllable_count
    }


@router.post("/rhymes/register", response_model=dict)
async def register_word_phonetics(data: PhoneticRegister, db: AsyncSession = Depends(get_db)):
    """Manually register or override a word in the MultisyllabicWord phonetic database"""
    from ..models import MultisyllabicWord
    
    # Check if entry already exists
    query = select(MultisyllabicWord).where(
        MultisyllabicWord.language == data.language,
        func.lower(MultisyllabicWord.word) == data.word.lower().strip()
    )
    res = await db.execute(query)
    word_entry = res.scalar_one_or_none()
    
    if word_entry:
        word_entry.vowel_sequence = data.vowel_sequence.strip()
        word_entry.exact_rhyme_key = data.exact_key.strip()
        word_entry.syllable_count = data.syllable_count
        word_entry.is_slang = data.is_slang
    else:
        word_entry = MultisyllabicWord(
            word=data.word.strip(),
            language=data.language,
            vowel_sequence=data.vowel_sequence.strip(),
            exact_rhyme_key=data.exact_key.strip(),
            syllable_count=data.syllable_count,
            is_slang=data.is_slang,
            upvotes=1
        )
        db.add(word_entry)
        
    try:
        await db.commit()
        _rhyme_detector.clear_cache()
        return {
            "success": True,
            "message": f"Successfully registered '{data.word}' in {data.language.upper()} dictionary."
        }
    except Exception as e:
        await db.rollback()
        return {"success": False, "error": str(e)}
