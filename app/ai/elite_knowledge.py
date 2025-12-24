"""
Elite Ghostwriting Knowledge Base
Curated techniques and few-shot examples for top-tier lyric generation.
NOTE: All examples are original, created for this application.
"""

# Hip-hop writing techniques with explanations
TECHNIQUES = {
    "multi_syllabic_rhyme": {
        "name": "Multi-Syllabic Rhyme",
        "description": "Rhyming multiple syllables across words for complex flow",
        "instruction": "Use 2-3 syllable rhyme patterns. Example: 'HOLLOW tips' / 'FOLLOW ships'",
    },
    "internal_rhyme": {
        "name": "Internal Rhyme",
        "description": "Rhymes within the same line, not just at the end",
        "instruction": "Include at least one internal rhyme per line. Connect words in the middle.",
    },
    "double_entendre": {
        "name": "Double Entendre", 
        "description": "Words or phrases with two meanings simultaneously",
        "instruction": "Use words that have both literal and figurative meanings.",
    },
    "metaphor_chains": {
        "name": "Extended Metaphor",
        "description": "Sustaining a single metaphor across multiple bars",
        "instruction": "Pick one metaphor theme and weave it through 4+ consecutive lines.",
    },
    "punchy_closers": {
        "name": "Punchy Line Endings",
        "description": "End lines with impactful, memorable words",
        "instruction": "End each line with a strong, visual, or emotionally charged word.",
    },
    "alliteration_flow": {
        "name": "Alliterative Flow",
        "description": "Repeating consonant sounds for rhythmic texture",
        "instruction": "Use 2-3 words starting with the same consonant per line.",
    },
    "syllable_control": {
        "name": "Syllable Precision",
        "description": "Matching syllable counts for consistent flow",
        "instruction": "Keep lines between 8-12 syllables. Match parallel lines exactly.",
    },
}

# Few-shot prompt examples (ORIGINAL content, not copyrighted)
# These are injected into prompts to guide the AI's style
FEW_SHOT_EXAMPLES = {
    "introspective": [
        {
            "context": "Reflecting on personal growth",
            "line": "Every scar I wear tells a story I survived",
            "technique": "metaphor + internal rhyme (wear/story)"
        },
        {
            "context": "Dealing with self-doubt",
            "line": "Mirror shows a stranger when the light hits wrong",
            "technique": "imagery + melancholy tone"
        },
    ],
    "confident": [
        {
            "context": "Asserting dominance",
            "line": "I was built for pressure, diamonds need the squeeze",
            "technique": "metaphor (diamond formation) + wordplay"
        },
        {
            "context": "Celebrating success",
            "line": "Started from the basement, now I own the building",
            "technique": "contrast + narrative arc"
        },
    ],
    "storytelling": [
        {
            "context": "Setting a scene",
            "line": "Three AM, cold streets, just me and my thoughts walking",
            "technique": "imagery + personification"
        },
        {
            "context": "Building tension",
            "line": "Phone rang twice then stopped, I knew the news was heavy",
            "technique": "detail + emotional buildup"
        },
    ],
    "wordplay": [
        {
            "context": "Clever bars",
            "line": "I'm raising the bar, they can't reach my level",
            "technique": "double meaning (bar = standard + pub)"
        },
        {
            "context": "Punchline setup",
            "line": "They say time is money, I'm investing every second",
            "technique": "idiom subversion + financial metaphor"
        },
    ],
}

# System prompt enhancement for elite ghostwriting
ELITE_SYSTEM_PROMPT = """You are an ELITE hip-hop ghostwriter with decades of experience.

CORE PRINCIPLES:
1. Every line must have PURPOSE - no filler words
2. Rhymes should feel NATURAL, not forced
3. Use CONCRETE imagery over abstract statements
4. Vary sentence structure to create dynamic flow
5. End lines with STRONG words (nouns, verbs) not weak ones (prepositions, articles)

ADVANCED TECHNIQUES TO APPLY:
- Multi-syllabic rhymes (2-3 syllable patterns)
- Internal rhymes (rhymes within lines)
- Strategic alliteration (2-3 words per line)
- Double meanings where appropriate
- Emotional authenticity over complexity

AVOID:
- Clichéd rhymes (love/above, flow/know, real/feel)
- Filler phrases ("you know", "like I said")
- Weak line endings (prepositions, "it", "the")
- Inconsistent syllable counts
- Abstract statements without imagery
"""

# Rhyme avoidance list (overused/cliché rhymes)
AVOID_RHYME_PAIRS = [
    ("love", "above"),
    ("heart", "start"),
    ("soul", "control"),
    ("mind", "find"),
    ("night", "right"),
    ("day", "way"),
    ("time", "rhyme"),
    ("flow", "know"),
    ("real", "feel"),
    ("game", "fame"),
    ("pain", "rain"),
    ("dream", "team"),
]

def get_technique_instructions(techniques: list) -> str:
    """Get instruction text for specific techniques"""
    instructions = []
    for tech in techniques:
        if tech in TECHNIQUES:
            t = TECHNIQUES[tech]
            instructions.append(f"- {t['name']}: {t['instruction']}")
    return "\n".join(instructions)

def get_few_shot_examples(mood: str, count: int = 2) -> str:
    """Get few-shot examples for a given mood"""
    examples = FEW_SHOT_EXAMPLES.get(mood, FEW_SHOT_EXAMPLES.get("wordplay", []))
    
    result = []
    for ex in examples[:count]:
        result.append(f"Context: {ex['context']}")
        result.append(f"Line: \"{ex['line']}\"")
        result.append(f"Technique: {ex['technique']}")
        result.append("")
    
    return "\n".join(result)

def get_elite_prompt_additions(mood: str = None, techniques: list = None) -> str:
    """
    Build additional prompt content for elite ghostwriting.
    This is injected into the AI's system/user prompt.
    """
    parts = [ELITE_SYSTEM_PROMPT]
    
    if mood and mood in FEW_SHOT_EXAMPLES:
        parts.append("\n## STYLE EXAMPLES (match this quality):")
        parts.append(get_few_shot_examples(mood))
    
    if techniques:
        parts.append("\n## REQUIRED TECHNIQUES:")
        parts.append(get_technique_instructions(techniques))
    
    # Add rhyme avoidance
    avoid_list = ", ".join([f"'{a}/{b}'" for a, b in AVOID_RHYME_PAIRS[:5]])
    parts.append(f"\n## AVOID THESE CLICHÉ RHYMES: {avoid_list}")
    
    return "\n".join(parts)
