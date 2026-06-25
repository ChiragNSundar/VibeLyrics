"""
Rhymes Router
Rhyme lookups, thesaurus, and multi-syllable rhymes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict
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
    target_syllables: Optional[int] = None
    target_stress: Optional[str] = None
    enable_semantic_reranking: bool = False
    context_text: Optional[str] = None


class RhymeVoteSchema(BaseModel):
    source_word: str
    target_word: str
    is_valid_rhyme: bool


@router.post("/rhymes/doppelreim", response_model=dict)
async def lookup_doppelreim(data: DoppelreimLookup, db: AsyncSession = Depends(get_db)):
    """Advanced multisyllabic lookup (Classic, Slant, Multi-word)"""
    results = await _rhyme_detector.find_doppelreim_rhymes(
        db, data.word, data.language, data.mode, data.allow_slang, data.max_results,
        data.target_syllables, data.target_stress,
        enable_semantic_reranking=data.enable_semantic_reranking,
        context_text=data.context_text
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
    target_words = [data.target_word.lower()]
    if " " in data.target_word:
        target_words.extend([w.strip().lower() for w in data.target_word.split(" ") if w.strip()])
        
    up_query = select(MultisyllabicWord).where(
        func.lower(MultisyllabicWord.word).in_(target_words)
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
    
    ipa_key = _rhyme_detector._normalize_to_ipa_key(data.vowel_sequence.strip(), data.language)
    
    if word_entry:
        word_entry.vowel_sequence = data.vowel_sequence.strip()
        word_entry.exact_rhyme_key = data.exact_key.strip()
        word_entry.syllable_count = data.syllable_count
        word_entry.is_slang = data.is_slang
        word_entry.ipa_key = ipa_key
    else:
        word_entry = MultisyllabicWord(
            word=data.word.strip(),
            language=data.language,
            vowel_sequence=data.vowel_sequence.strip(),
            exact_rhyme_key=data.exact_key.strip(),
            syllable_count=data.syllable_count,
            is_slang=data.is_slang,
            upvotes=1,
            ipa_key=ipa_key
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


class PhraseRhymeLookup(BaseModel):
    word: str
    language: str = "en"
    max_results: int = 20


class CrossLanguageLookup(BaseModel):
    word: str
    source_lang: str = "en"
    target_lang: str = "hi"
    max_results: int = 20


class DensityLookup(BaseModel):
    lines: List[str]


@router.post("/rhymes/phrase-rhyme", response_model=dict)
async def phrase_rhyme(data: PhraseRhymeLookup):
    """Generate on-the-fly compound phrase rhymes (e.g. 'orange' -> 'door hinge')"""
    results = _rhyme_detector.find_onthefly_phrase_rhymes(
        data.word, data.language, data.max_results
    )
    return {
        "success": True,
        "results": results
    }


@router.post("/rhymes/cross-language", response_model=dict)
async def cross_language_rhyme(data: CrossLanguageLookup, db: AsyncSession = Depends(get_db)):
    """Look up rhymes across languages using IPA-bridge matching"""
    results = await _rhyme_detector.find_cross_language_rhymes(
        db, data.word, data.source_lang, data.target_lang, data.max_results
    )
    return {
        "success": True,
        "results": results
    }


@router.post("/rhymes/density-detailed", response_model=dict)
async def density_detailed(data: DensityLookup):
    """Calculate detailed rhyme density heatmap with 0-100 scores and pair callouts"""
    heatmap = _rhyme_detector.get_density_heatmap(data.lines)
    return {
        "success": True,
        "heatmap": heatmap
    }


@router.get("/rhymes/autocomplete", response_model=dict)
async def autocomplete_rhymes(
    partial: str, prev_ending: str, language: str = "en", limit: int = 10, db: AsyncSession = Depends(get_db)
):
    """Suggest words starting with 'partial' that rhyme with 'prev_ending'"""
    results = await _rhyme_detector.autocomplete_rhyme(
        db, partial, prev_ending, language, limit
    )
    return {
        "success": True,
        "results": results
    }

