"""
Rhymes Router
Rhyme lookups, thesaurus, and multi-syllable rhymes
"""
from fastapi import APIRouter
from ..schemas import RhymeLookup, ThesaurusLookup
from ..services.rhyme_detector import RhymeDetector

router = APIRouter()
rhyme_detector = RhymeDetector()


@router.post("/rhymes/lookup", response_model=dict)
async def lookup_rhymes(data: RhymeLookup):
    """Look up rhymes for a word"""
    rhymes = rhyme_detector.find_rhymes(data.word, max_results=data.max_results)
    
    return {
        "success": True,
        "word": data.word,
        "rhymes": rhymes
    }


@router.get("/rhymes/{word}", response_model=dict)
async def get_rhymes(word: str, limit: int = 20):
    """Get rhymes for a word (simple endpoint)"""
    rhymes = rhyme_detector.find_rhymes(word, max_results=limit)
    
    return {
        "success": True,
        "word": word,
        "rhymes": rhymes
    }


@router.get("/rhymes/{word}/multi", response_model=dict)
async def get_multi_rhymes(word: str):
    """Get multi-syllable rhymes"""
    multi_rhymes = rhyme_detector.find_multi_syllable_rhymes(word)
    
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
        result["rhymes"] = rhyme_detector.find_rhymes(data.word)
    
    if data.include_synonyms:
        result["synonyms"] = rhyme_detector.get_synonyms(data.word)
    
    return result


@router.get("/slang/{category}", response_model=dict)
async def get_slang(category: str):
    """Get hip-hop slang for a category"""
    slang = rhyme_detector.get_slang_by_category(category)
    
    return {
        "success": True,
        "category": category,
        "slang": slang
    }


@router.get("/slang", response_model=dict)
async def get_slang_categories():
    """Get all slang categories"""
    categories = rhyme_detector.get_slang_categories()
    
    return {
        "success": True,
        "categories": categories
    }
