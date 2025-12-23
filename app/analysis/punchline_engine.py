"""
Punch Line Engine
Detects and generates hard-hitting punch lines with wordplay, contrast, and callbacks
"""
import re
from typing import List, Dict, Tuple, Optional
from collections import Counter

try:
    from nltk.corpus import wordnet as wn
except ImportError:
    wn = None


# Wordplay patterns that indicate punch line potential
CONTRAST_WORDS = {
    ("rich", "poor"), ("love", "hate"), ("life", "death"), ("real", "fake"),
    ("friend", "enemy"), ("king", "pawn"), ("rise", "fall"), ("weak", "strong"),
    ("start", "end"), ("first", "last"), ("hot", "cold"), ("dark", "light"),
    ("heaven", "hell"), ("bless", "curse"), ("win", "lose"), ("saint", "sinner")
}

# Double meaning words common in hip-hop
DOUBLE_MEANING_WORDS = {
    "bars": ["prison", "lyrics", "gold bars"],
    "ice": ["jewelry", "cold", "frozen"],
    "heat": ["gun", "temperature", "intensity"],
    "green": ["money", "envy", "nature"],
    "blue": ["sad", "police", "crip"],
    "red": ["blood", "anger", "love"],
    "cold": ["temperature", "ruthless", "style"],
    "fire": ["hot", "good", "gun"],
    "raw": ["uncooked", "real", "harsh"],
    "lit": ["fire", "drunk", "exciting"],
    "wave": ["ocean", "trend", "greeting"],
    "cake": ["dessert", "money", "booty"],
    "beef": ["meat", "conflict"],
    "sauce": ["condiment", "style", "drip"],
    "cap": ["hat", "lie", "bullet"],
    "heavy": ["weight", "serious", "deep"],
    "light": ["brightness", "easy", "not serious"],
    "high": ["elevation", "drugs", "status"],
    "low": ["depth", "sad", "sneaky"],
    "fly": ["insect", "cool", "travel"],
    "paper": ["document", "money"],
    "rock": ["stone", "diamond", "music"],
    "ball": ["sphere", "party", "basketball"],
    "roll": ["move", "money roll", "dice"],
    "shot": ["bullet", "drink", "chance"],
    "trunk": ["car", "tree", "elephant"],
    "check": ["money", "verify", "chess"]
}

# Punch line templates
PUNCHLINE_TEMPLATES = [
    "They said [X], I said [opposite]",
    "[Noun] so [adjective], [exaggeration]",
    "I got [thing] like [unexpected comparison]",
    "[Action] like [simile with twist]",
    "Call me [name] the way I [action]",
    "[Metaphor] but [literal twist]"
]


def detect_contrast(line: str) -> List[Tuple[str, str]]:
    """Detect contrasting word pairs in a line"""
    words = set(line.lower().split())
    found = []
    
    for w1, w2 in CONTRAST_WORDS:
        if w1 in words and w2 in words:
            found.append((w1, w2))
    
    return found


def detect_double_meanings(line: str) -> Dict[str, List[str]]:
    """Detect words with double meanings"""
    words = line.lower().split()
    found = {}
    
    for word in words:
        clean = word.strip('.,!?;:"\'')
        if clean in DOUBLE_MEANING_WORDS:
            found[clean] = DOUBLE_MEANING_WORDS[clean]
    
    return found


def detect_wordplay_patterns(line: str) -> List[Dict]:
    """Detect various wordplay patterns"""
    patterns = []
    line_lower = line.lower()
    
    # Alliteration (3+ words starting with same letter)
    words = [w.strip('.,!?;:"\'') for w in line.split()]
    if len(words) >= 3:
        first_letters = [w[0].lower() for w in words if w]
        letter_counts = Counter(first_letters)
        for letter, count in letter_counts.items():
            if count >= 3:
                patterns.append({
                    "type": "alliteration",
                    "letter": letter,
                    "count": count
                })
    
    # Homophones (words that sound alike)
    homophone_pairs = [
        ("there", "their", "they're"), ("your", "you're"), ("to", "too", "two"),
        ("know", "no"), ("write", "right"), ("won", "one"), ("son", "sun"),
        ("see", "sea"), ("by", "buy", "bye"), ("for", "four"), ("hear", "here"),
        ("break", "brake"), ("wait", "weight"), ("peace", "piece"), ("whole", "hole")
    ]
    for group in homophone_pairs:
        found_in_line = [w for w in group if w in line_lower]
        if len(found_in_line) >= 1:
            # Could be intentional wordplay
            patterns.append({
                "type": "homophone_potential",
                "words": list(group),
                "found": found_in_line
            })
    
    return patterns


def score_punchline(line: str) -> Dict:
    """
    Score punch line potential on a 1-10 scale with breakdown.
    """
    score = 0
    breakdown = []
    
    # Check for contrast
    contrasts = detect_contrast(line)
    if contrasts:
        score += 3
        breakdown.append(f"Contrast detected: {contrasts}")
    
    # Check for double meanings
    double_meanings = detect_double_meanings(line)
    if double_meanings:
        score += 2 * len(double_meanings)
        breakdown.append(f"Double meanings: {list(double_meanings.keys())}")
    
    # Check for wordplay patterns
    wordplay = detect_wordplay_patterns(line)
    if wordplay:
        score += len(wordplay)
        breakdown.append(f"Wordplay patterns: {len(wordplay)}")
    
    # Check line length (medium length often best for punch)
    word_count = len(line.split())
    if 6 <= word_count <= 12:
        score += 1
        breakdown.append("Optimal length for punch")
    
    # Check for exclamation (emphasis)
    if "!" in line:
        score += 1
        breakdown.append("Emphatic ending")
    
    # Cap at 10
    score = min(score, 10)
    
    return {
        "score": score,
        "rating": _get_rating(score),
        "breakdown": breakdown,
        "contrasts": contrasts,
        "double_meanings": double_meanings,
        "wordplay": wordplay
    }


def _get_rating(score: int) -> str:
    """Convert numeric score to rating"""
    if score >= 8:
        return "🔥 Legendary"
    elif score >= 6:
        return "💪 Hard"
    elif score >= 4:
        return "👍 Solid"
    elif score >= 2:
        return "📝 Potential"
    else:
        return "💭 Basic"


def generate_punchline_starters(theme: str, rhyme_word: Optional[str] = None) -> List[str]:
    """
    Generate punch line starter suggestions based on theme.
    """
    starters = []
    theme_lower = theme.lower()
    
    # Contrast-based starters
    starters.extend([
        f"They thought I'd fall, but I {theme_lower}",
        f"Started from the bottom, now I'm {theme_lower}",
        f"They sleeping on me, I'm {theme_lower}",
        f"Real recognize real, fake ones {theme_lower}"
    ])
    
    # Double meaning starters
    if theme_lower in DOUBLE_MEANING_WORDS:
        meanings = DOUBLE_MEANING_WORDS[theme_lower]
        starters.append(f"Got that {theme_lower} like {meanings[0]}, {meanings[-1]} too")
    
    # Simile starters
    starters.extend([
        f"I'm like {theme_lower} to these rappers",
        f"Move like {theme_lower}, flow like water",
        f"Heart of a lion, {theme_lower} of a G"
    ])
    
    # If rhyme word provided, add rhyme-conscious starters
    if rhyme_word:
        starters.append(f"[Complete this to rhyme with '{rhyme_word}']")
    
    return starters[:8]


def analyze_verse_for_punchlines(lines: List[str]) -> Dict:
    """
    Analyze entire verse to find best punch lines and suggest improvements.
    """
    results = []
    best_score = 0
    best_line_idx = 0
    
    for i, line in enumerate(lines):
        analysis = score_punchline(line)
        results.append({
            "line_index": i,
            "line": line,
            "score": analysis["score"],
            "rating": analysis["rating"],
            "has_double_meaning": len(analysis["double_meanings"]) > 0,
            "has_contrast": len(analysis["contrasts"]) > 0
        })
        
        if analysis["score"] > best_score:
            best_score = analysis["score"]
            best_line_idx = i
    
    return {
        "lines_analyzed": len(lines),
        "best_punchline_index": best_line_idx,
        "best_score": best_score,
        "line_scores": results,
        "avg_score": sum(r["score"] for r in results) / len(results) if results else 0
    }
