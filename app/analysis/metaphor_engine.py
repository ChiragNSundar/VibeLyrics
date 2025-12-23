"""
Metaphor/Simile Generator
Generates creative comparisons based on hip-hop themes and context
"""
import random
from typing import List, Dict, Optional


# Simile templates: "X like Y"
SIMILE_TEMPLATES = {
    "money": [
        "Money like water, it keep flowing",
        "Stacking like Legos, keep growing",
        "Cash like leaves in the fall",
        "Bread like a bakery, got it all",
        "Paper like a printer, never stall"
    ],
    "speed": [
        "Fast like lightning, can't catch me",
        "Quick like Sonic, running free",
        "Move like the wind, you can't see",
        "Swift like a bullet, MVP",
        "Rapid like fire, burning speed"
    ],
    "cold": [
        "Cold like December, no pretender",
        "Ice like winter, I remember",
        "Frozen like the Arctic, no surrender",
        "Chill like the North, heart of ember",
        "Cool as a breeze in September"
    ],
    "hot": [
        "Hot like the sun, I'm the one",
        "Fire like Phoenix, never done",
        "Burning like flames, on the run",
        "Heat like summer, having fun",
        "Blazing trails, watch me stun"
    ],
    "hard": [
        "Hard like a diamond, can't crack",
        "Solid as rock, that's a fact",
        "Tough like titanium, no slack",
        "Strong like steel, on attack",
        "Unbreakable, never fall back"
    ],
    "smooth": [
        "Smooth like butter, no stutter",
        "Silky like velvet, make 'em flutter",
        "Clean like crystal, never clutter",
        "Fresh like morning, hear 'em mutter",
        "Flow like water through the gutter"
    ],
    "high": [
        "High like mountains, I'm the peak",
        "Up like eagles, watch me speak",
        "Elevated, ain't no weak",
        "Top of the world, what I seek",
        "Cloud nine daily, every week"
    ],
    "real": [
        "Real like facts, no fiction",
        "True like the sun, no friction",
        "Authentic, got that conviction",
        "Genuine, no contradiction",
        "Honest, call it my addiction"
    ]
}

# Metaphor mappings: concept → metaphorical representations
METAPHOR_MAPPINGS = {
    "success": ["throne", "crown", "mountain top", "finish line", "gold", "summit", "kingdom"],
    "struggle": ["storm", "battle", "desert", "darkness", "ocean", "fire", "war zone"],
    "money": ["paper", "bread", "cake", "green", "bands", "racks", "stacks"],
    "love": ["fire", "ocean", "drug", "paradise", "heaven", "magic", "spell"],
    "life": ["journey", "game", "movie", "book", "road", "story", "chapter"],
    "death": ["sleep", "darkness", "silence", "void", "end credits", "final chapter"],
    "fame": ["spotlight", "stage", "throne", "crown", "pedestal", "summit"],
    "power": ["throne", "crown", "scepter", "iron fist", "kingdom", "empire"],
    "wisdom": ["light", "key", "compass", "map", "treasure", "gold"],
    "time": ["river", "thief", "sand", "wind", "ghost", "enemy"],
    "enemy": ["snake", "rat", "demon", "shadow", "parasite", "disease"],
    "friend": ["soldier", "brother", "rock", "shield", "family", "day one"],
    "music": ["medicine", "therapy", "drug", "weapon", "magic", "prayer"],
    "hustle": ["grind", "marathon", "hunt", "mission", "war", "chess game"],
    "loyalty": ["gold", "diamond", "blood", "oath", "bond", "armor"]
}

# Extended metaphor starters
METAPHOR_STARTERS = [
    "I am the {metaphor}, {action}",
    "They call me {metaphor}, I {action}",
    "Life's a {metaphor}, and I'm {role}",
    "This game's a {metaphor}, I'm the {role}",
    "My mind is a {metaphor}, {description}",
    "Heart of a {metaphor}, soul of a {metaphor2}",
    "Built like a {metaphor}, think like a {metaphor2}"
]


def generate_similes(word: str, count: int = 5) -> List[str]:
    """
    Generate simile suggestions for a given word.
    
    Args:
        word: The base word/concept
        count: Number of suggestions to return
    """
    word_lower = word.lower()
    
    # Check if we have templates for this word
    if word_lower in SIMILE_TEMPLATES:
        templates = SIMILE_TEMPLATES[word_lower]
        return random.sample(templates, min(count, len(templates)))
    
    # Generate dynamic similes
    similes = [
        f"{word} like the [noun], I [verb]",
        f"Moving like {word}, can't stop",
        f"Got that {word} flow, on top",
        f"Feel like {word}, never drop",
        f"Stay {word} 24/7, non-stop"
    ]
    
    return similes[:count]


def generate_metaphors(concept: str, count: int = 5) -> List[Dict]:
    """
    Generate metaphor suggestions for a concept.
    """
    concept_lower = concept.lower()
    results = []
    
    # Get metaphor mappings
    if concept_lower in METAPHOR_MAPPINGS:
        metaphors = METAPHOR_MAPPINGS[concept_lower]
        
        for metaphor in metaphors[:count]:
            results.append({
                "metaphor": metaphor,
                "example": f"My {concept_lower} is a {metaphor}",
                "extended": f"I'm the {metaphor} of this {concept_lower}"
            })
    else:
        # Generate generic metaphors
        generic = ["fire", "storm", "king", "warrior", "champion"]
        for m in generic[:count]:
            results.append({
                "metaphor": m,
                "example": f"I'm the {m} when it comes to {concept_lower}",
                "extended": f"{concept.title()} runs through me like {m}"
            })
    
    return results


def complete_simile(starter: str) -> List[str]:
    """
    Complete a simile that starts with "X like..."
    
    Args:
        starter: e.g., "Money like" or "I move like"
    """
    completions = []
    
    # Extract what comes before "like"
    if " like" in starter.lower():
        subject = starter.lower().split(" like")[0].strip().split()[-1]
    else:
        subject = starter.lower().strip()
    
    # Common hip-hop simile completions
    endings = [
        "water, flowing free",
        "Jordan, MVP",
        "a lion, king of the scene",
        "a rocket, extreme",
        "thunder, making noise",
        "magic, got the poise",
        "a legend, never fade",
        "the sun, always stay",
        "a boss, running things",
        "royalty, with the rings"
    ]
    
    for ending in endings[:5]:
        completions.append(f"{starter} {ending}")
    
    return completions


def analyze_metaphor_density(lines: List[str]) -> Dict:
    """
    Analyze how many metaphors/similes are in a verse.
    """
    simile_count = 0
    metaphor_indicators = 0
    
    for line in lines:
        line_lower = line.lower()
        
        # Count similes (word "like" or "as")
        if " like " in line_lower or " as a " in line_lower or " as the " in line_lower:
            simile_count += 1
        
        # Count metaphor indicators
        for concept, metaphors in METAPHOR_MAPPINGS.items():
            for m in metaphors:
                if m in line_lower:
                    metaphor_indicators += 1
                    break
    
    total_lines = len(lines)
    density = (simile_count + metaphor_indicators) / total_lines if total_lines > 0 else 0
    
    return {
        "total_lines": total_lines,
        "similes_found": simile_count,
        "metaphor_indicators": metaphor_indicators,
        "density": round(density, 2),
        "rating": _get_density_rating(density)
    }


def _get_density_rating(density: float) -> str:
    """Rating for metaphor density"""
    if density >= 0.5:
        return "🔥 Highly Figurative"
    elif density >= 0.3:
        return "💪 Strong Imagery"
    elif density >= 0.15:
        return "👍 Good Balance"
    else:
        return "📝 Could use more imagery"


def suggest_imagery_for_line(line: str) -> Dict:
    """
    Suggest ways to add metaphors/similes to a plain line.
    """
    words = line.lower().split()
    suggestions = []
    
    # Find concepts that could be metaphorized
    for word in words:
        clean = word.strip('.,!?;:"\'')
        if clean in METAPHOR_MAPPINGS:
            metaphors = METAPHOR_MAPPINGS[clean]
            suggestions.append({
                "word": clean,
                "type": "metaphor",
                "options": metaphors[:3]
            })
    
    # Suggest adding similes
    simile_suggestion = None
    for word in words:
        if len(word) > 3 and word not in ["like", "the", "and", "but", "for"]:
            simile_suggestion = f"Try: '{word} like [comparison]'"
            break
    
    return {
        "original": line,
        "metaphor_opportunities": suggestions,
        "simile_suggestion": simile_suggestion,
        "has_imagery": len(suggestions) > 0 or " like " in line.lower()
    }
