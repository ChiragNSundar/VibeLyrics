"""
Multi-Syllable Rhyme Finder
Finds complex multi-syllabic rhymes like professional rappers use
"""
import pronouncing
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


def get_phonemes(word: str) -> Optional[str]:
    """Get phonemes for a word"""
    try:
        phones = pronouncing.phones_for_word(word.lower())
        if phones:
            return phones[0]
        return None
    except Exception:
        return None


def get_rhyme_part(phonemes: str, syllables: int = 2) -> str:
    """
    Extract the rhyming part (last N syllables) from phonemes.
    Vowels with numbers indicate stressed syllables.
    """
    if not phonemes:
        return ""
    
    parts = phonemes.split()
    
    # Find vowel positions (vowels have numbers 0, 1, 2 for stress)
    vowel_positions = []
    for i, part in enumerate(parts):
        if any(c.isdigit() for c in part):
            vowel_positions.append(i)
    
    if len(vowel_positions) < syllables:
        # Word has fewer syllables than requested
        return phonemes
    
    # Get from the Nth-to-last vowel onwards
    start_pos = vowel_positions[-syllables]
    return " ".join(parts[start_pos:])


def find_multi_rhymes(word: str, syllables: int = 2, max_results: int = 20) -> Dict:
    """
    Find words that rhyme on multiple syllables.
    
    Args:
        word: The word to find rhymes for
        syllables: Number of syllables to match (2, 3, 4+)
        max_results: Maximum number of results
        
    Returns:
        {
            "query": str,
            "syllables_matched": int,
            "rhymes": [{"word": str, "score": int, "phoneme_match": str}]
        }
    """
    phonemes = get_phonemes(word)
    
    if not phonemes:
        return {
            "query": word,
            "syllables_matched": syllables,
            "rhymes": [],
            "error": "Could not find pronunciation"
        }
    
    target_rhyme_part = get_rhyme_part(phonemes, syllables)
    
    # Get all standard rhymes first
    try:
        basic_rhymes = pronouncing.rhymes(word.lower())
    except Exception:
        basic_rhymes = []
    
    # Score each rhyme by how many syllables match
    scored_rhymes = []
    
    for rhyme in basic_rhymes:
        rhyme_phonemes = get_phonemes(rhyme)
        if not rhyme_phonemes:
            continue
        
        # Check how many syllables match
        rhyme_part = get_rhyme_part(rhyme_phonemes, syllables)
        
        # Count matching phonemes from the end
        target_parts = target_rhyme_part.split()
        rhyme_parts = rhyme_part.split()
        
        matching = 0
        for t, r in zip(reversed(target_parts), reversed(rhyme_parts)):
            # Strip stress markers for comparison
            t_clean = ''.join(c for c in t if not c.isdigit())
            r_clean = ''.join(c for c in r if not c.isdigit())
            if t_clean == r_clean:
                matching += 1
            else:
                break
        
        if matching >= syllables:
            scored_rhymes.append({
                "word": rhyme,
                "score": matching,
                "phoneme_match": rhyme_part
            })
    
    # Sort by score descending
    scored_rhymes.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "query": word,
        "syllables_matched": syllables,
        "target_phonemes": target_rhyme_part,
        "rhymes": scored_rhymes[:max_results]
    }


def find_phrase_rhymes(phrase: str, max_results: int = 10) -> Dict:
    """
    Find phrases that rhyme with a multi-word phrase.
    Matches ending sounds across word boundaries.
    
    Example: "elevation" → "celebration", "devastation"
    Example: "real life" → "steel knife", "feel right"
    """
    words = phrase.lower().split()
    
    if not words:
        return {"query": phrase, "matches": []}
    
    # Get the last word for primary rhyming
    last_word = words[-1].strip('.,!?;:"\'')
    
    # Find multi-syllable rhymes for last word
    multi_results = find_multi_rhymes(last_word, syllables=2, max_results=max_results * 2)
    
    matches = []
    for rhyme_info in multi_results.get("rhymes", []):
        rhyme_word = rhyme_info["word"]
        
        # For single word phrases, just return the rhyme
        if len(words) == 1:
            matches.append({
                "phrase": rhyme_word,
                "score": rhyme_info["score"]
            })
        else:
            # For multi-word phrases, try to create a matching phrase
            # This is a simplified version - could be enhanced with more sophisticated matching
            matches.append({
                "phrase": rhyme_word,
                "score": rhyme_info["score"],
                "note": f"Rhymes with '{last_word}'"
            })
    
    return {
        "query": phrase,
        "matches": matches[:max_results]
    }


# Pre-built multi-syllable rhyme families for common hip-hop words
MULTI_RHYME_FAMILIES = {
    "elevation": ["celebration", "dedication", "devastation", "meditation", "revelation", 
                  "operation", "separation", "generation", "conversation", "destination"],
    "situation": ["education", "motivation", "reputation", "imagination", "foundation",
                  "concentration", "population", "information", "fascination", "domination"],
    "legendary": ["cemetery", "beneficiary", "extraordinary", "missionary", "visionary",
                  "stationary", "sanctuary", "mercenary", "solitary", "obituary"],
    "incredible": ["edible", "responsible", "accessible", "flexible", "terrible",
                   "horrible", "impossible", "invisible", "invincible", "susceptible"],
    "opportunity": ["community", "immunity", "unity", "impunity", "continuity"],
    "mentality": ["reality", "brutality", "fatality", "vitality", "immortality", 
                  "originality", "hospitality", "personality", "nationality", "morality"]
}


def get_rhyme_family(word: str) -> List[str]:
    """Get pre-built rhyme family for common multi-syllable endings"""
    word_lower = word.lower()
    
    # Check if word is in any family
    for key_word, family in MULTI_RHYME_FAMILIES.items():
        if word_lower == key_word or word_lower in family:
            # Return family excluding the query word
            return [w for w in [key_word] + family if w != word_lower]
    
    # Check for common endings
    for ending in ["ation", "ity", "ary", "ible", "able"]:
        if word_lower.endswith(ending):
            # Find words with same ending from families
            matches = []
            for key_word, family in MULTI_RHYME_FAMILIES.items():
                if key_word.endswith(ending):
                    matches.extend([key_word] + family)
            return [w for w in matches if w != word_lower][:15]
    
    return []


def suggest_multi_rhyme(word: str) -> Dict:
    """
    Comprehensive multi-rhyme suggestion including families and dynamic search.
    """
    # Try pre-built families first (faster)
    family = get_rhyme_family(word)
    
    # Also do dynamic search
    dynamic_2 = find_multi_rhymes(word, syllables=2, max_results=10)
    dynamic_3 = find_multi_rhymes(word, syllables=3, max_results=10)
    
    return {
        "word": word,
        "rhyme_family": family[:10],
        "2_syllable_matches": [r["word"] for r in dynamic_2.get("rhymes", [])],
        "3_syllable_matches": [r["word"] for r in dynamic_3.get("rhymes", [])]
    }
