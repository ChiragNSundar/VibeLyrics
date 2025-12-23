"""
Auto-Adlib Generator
Generates contextual adlibs for lyric lines based on patterns and energy
"""
import re
import random
from typing import List, Dict, Tuple


# Adlib libraries organized by mood/energy
ADLIB_LIBRARY = {
    "hype": [
        "Yeah!", "What!", "Aye!", "Let's go!", "Woo!", "Skrrt!", 
        "Brr!", "Gang!", "Facts!", "Period!", "No cap!", "Sheesh!",
        "Ayy!", "Uh!", "Yuh!", "Big!", "That's it!", "Talk to 'em!"
    ],
    "flex": [
        "Ice!", "Drip!", "Cash!", "Money!", "Bands!", "Racks!",
        "Rich!", "Paid!", "Ballin!", "Boss!", "Check!", "Foreign!"
    ],
    "aggressive": [
        "Bow!", "Pow!", "Bang!", "Grr!", "Blatt!", "Boom!",
        "Smoke!", "Gang!", "On God!", "Real!", "Facts!", "No lie!"
    ],
    "smooth": [
        "Mmm", "Yeah...", "Ooh", "Baby", "Aye", "You know",
        "That's right", "Mmhmm", "Feel me", "Vibes", "Smooth"
    ],
    "emotional": [
        "Pain...", "Real...", "Damn...", "Feel it", "Heart", 
        "Soul", "Deep", "True", "Honest", "Raw"
    ],
    "ending": [
        "!", "Gang!", "Yeah!", "Out!", "Peace!", "Gone!",
        "Facts!", "Period!", "Real talk!", "That's it!"
    ],
    "filler": [
        "Uh", "Yeah", "Aye", "Mmm", "Like", "You know",
        "I said", "Look", "Check it", "Listen"
    ]
}

# Words/patterns that trigger specific adlib types
TRIGGER_PATTERNS = {
    "hype": [
        r'\b(lit|fire|hot|crazy|insane|wild|turnt|gas)\b',
        r'\b(let.?s go|run it|we here|on top)\b',
        r'!$'
    ],
    "flex": [
        r'\b(money|cash|bands|racks|rich|paid|ice|drip|chain|watch|whip|foreign)\b',
        r'\b(million|thousand|designer|gucci|louis)\b'
    ],
    "aggressive": [
        r'\b(kill|dead|smoke|beef|war|opps|enemy|gun|strap|heat)\b',
        r'\b(never|won.?t|can.?t stop|don.?t play)\b'
    ],
    "smooth": [
        r'\b(love|baby|girl|shawty|vibe|chill|relax|slow)\b',
        r'\b(tonight|feeling|mood|zone)\b'
    ],
    "emotional": [
        r'\b(pain|hurt|cry|tears|lost|miss|remember|gone|death|die)\b',
        r'\b(heart|soul|deep|real|truth|honest)\b'
    ]
}

# Rhyme-end words that often get emphasized
EMPHASIS_ENDINGS = [
    "ing", "ight", "ay", "ee", "ow", "ine", "ack", "ade"
]


def detect_mood(line: str) -> str:
    """Detect the mood of a line based on patterns"""
    line_lower = line.lower()
    
    scores = {mood: 0 for mood in TRIGGER_PATTERNS}
    
    for mood, patterns in TRIGGER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, line_lower, re.IGNORECASE):
                scores[mood] += 1
    
    # Get mood with highest score
    max_mood = max(scores, key=scores.get)
    
    # If no strong signal, default to hype
    if scores[max_mood] == 0:
        return "hype"
    
    return max_mood


def get_random_adlib(mood: str, exclude: List[str] = None) -> str:
    """Get a random adlib for the given mood"""
    if exclude is None:
        exclude = []
    
    options = [a for a in ADLIB_LIBRARY.get(mood, ADLIB_LIBRARY["hype"]) 
               if a not in exclude]
    
    if not options:
        options = ADLIB_LIBRARY["hype"]
    
    return random.choice(options)


def find_adlib_positions(line: str) -> List[Tuple[int, str]]:
    """
    Find good positions for adlibs in a line.
    Returns list of (position, type) tuples.
    """
    positions = []
    words = line.split()
    
    if not words:
        return positions
    
    # End of line is always a good spot
    positions.append((len(line), "ending"))
    
    # After punctuation (comma, dash)
    for match in re.finditer(r'[,\-–]', line):
        positions.append((match.end(), "filler"))
    
    # After emphasized words (all caps, long words)
    word_positions = []
    current_pos = 0
    for word in words:
        word_start = line.find(word, current_pos)
        word_end = word_start + len(word)
        
        # Check if word is emphasized (all caps)
        if word.isupper() and len(word) > 2:
            positions.append((word_end, "hype"))
        
        # Check for rhyme-ending words
        clean_word = word.strip('.,!?;:"\'').lower()
        for ending in EMPHASIS_ENDINGS:
            if clean_word.endswith(ending):
                positions.append((word_end, "ending"))
                break
        
        current_pos = word_end
    
    return positions


def generate_adlibs(line: str, intensity: str = "medium") -> Dict:
    """
    Generate adlib suggestions for a single line.
    
    Args:
        line: The lyric line
        intensity: "low", "medium", or "high" - controls adlib density
        
    Returns:
        {
            "original": str,
            "with_adlibs": str,
            "adlibs_used": [str],
            "mood_detected": str
        }
    """
    if not line.strip():
        return {
            "original": line,
            "with_adlibs": line,
            "adlibs_used": [],
            "mood_detected": "neutral"
        }
    
    mood = detect_mood(line)
    positions = find_adlib_positions(line)
    
    # Determine how many adlibs based on intensity
    max_adlibs = {"low": 1, "medium": 2, "high": 3}.get(intensity, 2)
    
    # Sort positions by preference (endings first)
    positions.sort(key=lambda x: (x[1] != "ending", -x[0]))
    
    # Select positions up to max
    selected = positions[:max_adlibs]
    
    # Build the line with adlibs, working backwards to preserve positions
    selected.sort(key=lambda x: x[0], reverse=True)
    
    result = line
    adlibs_used = []
    
    for pos, adlib_type in selected:
        adlib = get_random_adlib(mood if adlib_type != "filler" else "filler", adlibs_used)
        adlibs_used.append(adlib)
        
        # Insert adlib in parentheses
        result = result[:pos] + f" ({adlib})" + result[pos:]
    
    return {
        "original": line,
        "with_adlibs": result.strip(),
        "adlibs_used": adlibs_used,
        "mood_detected": mood
    }


def generate_adlibs_for_verse(lines: List[str], intensity: str = "medium") -> Dict:
    """
    Generate adlibs for an entire verse.
    
    Args:
        lines: List of lyric lines
        intensity: "low", "medium", or "high"
        
    Returns:
        {
            "original_lines": [str],
            "lines_with_adlibs": [str],
            "adlib_suggestions": [{"line_index": int, "adlibs": [str]}],
            "overall_mood": str
        }
    """
    if not lines:
        return {
            "original_lines": [],
            "lines_with_adlibs": [],
            "adlib_suggestions": [],
            "overall_mood": "neutral"
        }
    
    # Detect overall mood from all lines
    combined = " ".join(lines)
    overall_mood = detect_mood(combined)
    
    results = []
    lines_with_adlibs = []
    suggestions = []
    
    for i, line in enumerate(lines):
        result = generate_adlibs(line, intensity)
        results.append(result)
        lines_with_adlibs.append(result["with_adlibs"])
        
        if result["adlibs_used"]:
            suggestions.append({
                "line_index": i,
                "adlibs": result["adlibs_used"],
                "mood": result["mood_detected"]
            })
    
    return {
        "original_lines": lines,
        "lines_with_adlibs": lines_with_adlibs,
        "adlib_suggestions": suggestions,
        "overall_mood": overall_mood
    }


def get_adlib_for_context(context: str, previous_adlibs: List[str] = None) -> str:
    """
    Get a contextually appropriate adlib based on preceding text.
    Useful for real-time suggestion as user types.
    """
    if previous_adlibs is None:
        previous_adlibs = []
    
    mood = detect_mood(context)
    return get_random_adlib(mood, previous_adlibs)
