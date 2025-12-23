"""
Semantic Concept Rhymes
Suggests words that rhyme AND relate conceptually using WordNet
"""
from typing import List, Dict, Set
import pronouncing

try:
    from nltk.corpus import wordnet as wn
    from nltk import download
    # Ensure wordnet is available
    try:
        wn.synsets('test')
    except LookupError:
        download('wordnet', quiet=True)
        download('omw-1.4', quiet=True)
except ImportError:
    wn = None


# Hip-hop specific concept mappings (not in WordNet)
HIP_HOP_CONCEPTS = {
    "money": ["bands", "racks", "paper", "bread", "cake", "guap", "cheese", "dough", "green", "stacks", "bills", "cash", "bucks"],
    "car": ["whip", "ride", "foreign", "lambo", "coupe", "drop", "vert", "beamer", "benz", "wraith"],
    "gun": ["strap", "pole", "heat", "piece", "iron", "nine", "glock", "tool", "stick", "blick"],
    "jewelry": ["ice", "drip", "chains", "rocks", "bling", "bust", "froze", "flooded", "piece"],
    "drugs": ["loud", "gas", "pack", "za", "percs", "lean", "drank", "mud", "syrup"],
    "success": ["wins", "bags", "goals", "crown", "throne", "top", "peak", "wave", "glow"],
    "king": ["throne", "crown", "reign", "kingdom", "royalty", "ruler", "majesty", "empire"],
    "queen": ["throne", "crown", "reign", "royalty", "goddess", "empress", "majesty"],
    "love": ["heart", "soul", "feelings", "emotions", "passion", "devotion", "affection"],
    "enemy": ["opps", "haters", "snakes", "foes", "rivals", "fakes", "clowns"],
    "friends": ["squad", "gang", "crew", "bros", "team", "circle", "fam", "homies"],
    "home": ["hood", "block", "streets", "city", "town", "ends", "turf", "stomping grounds"],
    "woman": ["queen", "shawty", "shorty", "wifey", "lady", "dime", "goddess"],
    "man": ["king", "dude", "bro", "homie", "player", "boss", "chief"],
    "fight": ["beef", "war", "smoke", "static", "clash", "battle", "scrap"],
    "police": ["cops", "laws", "feds", "12", "five-o", "pigs", "jakes"],
    "prison": ["pen", "joint", "cage", "cell", "time", "bid", "locked"],
    "rich": ["wealthy", "loaded", "paid", "ballin", "blessed", "set", "eatin"],
    "poor": ["broke", "starving", "struggling", "hungry", "down", "low"],
    "death": ["grave", "coffin", "rip", "gone", "departed", "fallen", "lost"],
    "life": ["living", "breathing", "existing", "journey", "path", "story"],
}


def get_wordnet_related(word: str) -> Set[str]:
    """Get semantically related words from WordNet"""
    if wn is None:
        return set()
    
    related = set()
    
    for synset in wn.synsets(word.lower()):
        # Synonyms (lemmas in same synset)
        for lemma in synset.lemmas():
            name = lemma.name().replace('_', ' ')
            if name.lower() != word.lower():
                related.add(name.lower())
        
        # Hypernyms (broader terms)
        for hyper in synset.hypernyms():
            for lemma in hyper.lemmas():
                related.add(lemma.name().replace('_', ' ').lower())
        
        # Hyponyms (more specific terms)
        for hypo in synset.hyponyms():
            for lemma in hypo.lemmas():
                related.add(lemma.name().replace('_', ' ').lower())
        
        # Related forms (derivationally related)
        for lemma in synset.lemmas():
            for related_form in lemma.derivationally_related_forms():
                related.add(related_form.name().replace('_', ' ').lower())
    
    return related


def get_hip_hop_related(word: str) -> Set[str]:
    """Get hip-hop culture related words"""
    related = set()
    word_lower = word.lower()
    
    # Direct lookup
    if word_lower in HIP_HOP_CONCEPTS:
        related.update(HIP_HOP_CONCEPTS[word_lower])
    
    # Reverse lookup (find categories containing this word)
    for category, words in HIP_HOP_CONCEPTS.items():
        if word_lower in words:
            related.add(category)
            related.update(words)
    
    return related


def get_concept_cluster(word: str) -> Dict[str, List[str]]:
    """
    Get all semantically related words organized by source.
    
    Returns:
        {
            "wordnet": [...],
            "hip_hop": [...],
            "all": [...]
        }
    """
    wordnet_words = get_wordnet_related(word)
    hip_hop_words = get_hip_hop_related(word)
    
    # Remove the original word from results
    wordnet_words.discard(word.lower())
    hip_hop_words.discard(word.lower())
    
    all_words = wordnet_words | hip_hop_words
    
    return {
        "wordnet": sorted(list(wordnet_words))[:20],
        "hip_hop": sorted(list(hip_hop_words))[:20],
        "all": sorted(list(all_words))[:30]
    }


def get_rhyming_words(word: str) -> Set[str]:
    """Get words that rhyme with the given word"""
    rhymes = set()
    
    try:
        rhymes.update(pronouncing.rhymes(word.lower()))
    except Exception:
        pass
    
    return rhymes


def get_concept_rhymes(word: str, max_results: int = 15) -> Dict[str, any]:
    """
    Get words that BOTH rhyme AND are semantically related.
    This is the "holy grail" of lyric writing assistance.
    
    Args:
        word: The word to find concept rhymes for
        max_results: Maximum number of results
        
    Returns:
        {
            "concept_rhymes": [...],  # Words that rhyme AND relate
            "related_only": [...],    # Semantically related but don't rhyme
            "rhymes_only": [...],     # Rhyme but not semantically related
            "original_word": str
        }
    """
    # Get all related words
    concept_cluster = get_concept_cluster(word)
    all_related = set(concept_cluster["all"])
    
    # Get all rhyming words
    rhyming = get_rhyming_words(word)
    
    # Find the intersection - words that both rhyme AND relate
    concept_rhymes = all_related & rhyming
    
    # Words that only relate (for "concept suggestions")
    related_only = all_related - rhyming
    
    # Words that only rhyme (standard rhymes)
    rhymes_only = rhyming - all_related
    
    return {
        "concept_rhymes": sorted(list(concept_rhymes))[:max_results],
        "related_only": sorted(list(related_only))[:max_results],
        "rhymes_only": sorted(list(rhymes_only))[:max_results],
        "original_word": word,
        "hip_hop_related": concept_cluster["hip_hop"][:10]
    }


def build_mind_map(lines: List[str]) -> Dict[str, List[str]]:
    """
    Build a "mind map" of concepts from a verse.
    Extracts key words and finds their semantic clusters.
    
    Args:
        lines: List of lyric lines
        
    Returns:
        {
            "core_concepts": [...],
            "expanded_concepts": {...}
        }
    """
    # Simple extraction of meaningful words
    all_words = []
    for line in lines:
        words = line.lower().split()
        # Filter to meaningful words (length > 3, not common words)
        common = {"the", "and", "but", "for", "with", "that", "this", "from", "have", "been", "were", "they", "them", "like", "just", "when", "what", "where", "your", "about"}
        meaningful = [w.strip('.,!?;:"\'') for w in words 
                     if len(w) > 3 and w.strip('.,!?;:"\'').lower() not in common]
        all_words.extend(meaningful)
    
    # Count word frequency to find core concepts
    from collections import Counter
    word_counts = Counter(all_words)
    core_concepts = [word for word, count in word_counts.most_common(5)]
    
    # Expand each core concept
    expanded = {}
    for concept in core_concepts:
        cluster = get_concept_cluster(concept)
        expanded[concept] = cluster["all"][:10]
    
    return {
        "core_concepts": core_concepts,
        "expanded_concepts": expanded
    }
