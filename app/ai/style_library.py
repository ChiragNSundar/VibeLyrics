"""
Style Library
Artist style definitions for Style Transfer feature
"""
from typing import Dict, List, Optional

# Artist style definitions with writing characteristics
ARTIST_STYLES = {
    "eminem": {
        "name": "Eminem",
        "icon": "🔥",
        "description": "Complex rhyme schemes, rapid-fire delivery, personal/emotional content",
        "characteristics": {
            "rhyme_density": "very_high",
            "multisyllabic": True,
            "internal_rhymes": True,
            "storytelling": True,
            "wordplay": "extreme",
            "syllables_per_line": (12, 20),
            "vocabulary": "complex"
        },
        "style_prompt": """Write in Eminem's style:
- Use complex multi-syllabic rhyme schemes (3-4 syllable rhymes)
- Include internal rhymes within lines
- Be emotionally raw and confessional
- Use clever wordplay and double meanings
- Pack maximum syllables per bar
- Mix humor with dark themes
- Reference personal struggles""",
        "example_patterns": [
            "I'm not afraid to take a stand, everybody come take my hand",
            "His palms are sweaty, knees weak, arms are heavy",
            "Look, if you had one shot, or one opportunity"
        ],
        "avoid": ["simple rhymes", "generic themes", "short lines"]
    },
    
    "kendrick": {
        "name": "Kendrick Lamar",
        "icon": "👑",
        "description": "Conscious lyrics, complex flows, storytelling, jazz influences",
        "characteristics": {
            "rhyme_density": "high",
            "multisyllabic": True,
            "internal_rhymes": True,
            "storytelling": True,
            "wordplay": "conceptual",
            "syllables_per_line": (10, 16),
            "vocabulary": "intellectual"
        },
        "style_prompt": """Write in Kendrick Lamar's style:
- Use conceptual wordplay with deeper meanings
- Include social commentary and consciousness
- Employ varied flow patterns (switch up rhythms)
- Tell vivid stories with specific details
- Reference Compton/LA culture
- Use metaphors that require interpretation
- Balance aggression with introspection""",
        "example_patterns": [
            "Sit down. Be humble.",
            "We gon' be alright",
            "How much a dollar cost, the question is detour"
        ],
        "avoid": ["surface-level lyrics", "predictable flows"]
    },
    
    "drake": {
        "name": "Drake",
        "icon": "🦉",
        "description": "Melodic flows, emotional vulnerability, catchy hooks",
        "characteristics": {
            "rhyme_density": "medium",
            "multisyllabic": False,
            "internal_rhymes": False,
            "storytelling": False,
            "wordplay": "subtle",
            "syllables_per_line": (8, 14),
            "vocabulary": "accessible"
        },
        "style_prompt": """Write in Drake's style:
- Use smooth, melodic phrasing
- Be emotionally vulnerable about relationships
- Reference luxury, success, and past struggles
- Create quotable, meme-worthy lines
- Mix singing cadence with rapping
- Reference Toronto/OVO
- Use repetition for emphasis""",
        "example_patterns": [
            "Started from the bottom now we're here",
            "You used to call me on my cell phone",
            "I got my mind on my money and I'm not going"
        ],
        "avoid": ["overly complex rhymes", "aggressive delivery"]
    },
    
    "jcole": {
        "name": "J. Cole",
        "icon": "🌲",
        "description": "Storytelling, introspective, conscious hip-hop",
        "characteristics": {
            "rhyme_density": "high",
            "multisyllabic": True,
            "internal_rhymes": True,
            "storytelling": True,
            "wordplay": "thoughtful",
            "syllables_per_line": (10, 16),
            "vocabulary": "relatable"
        },
        "style_prompt": """Write in J. Cole's style:
- Tell complete stories with beginning, middle, end
- Be introspective and self-reflective
- Reference humble beginnings and growth
- Use extended metaphors throughout verses
- Include social commentary
- Balance braggadocio with wisdom
- Reference Fayetteville/North Carolina""",
        "example_patterns": [
            "Middle child, I'm the reason",
            "Love yourz, no such thing as a life that's better than yourz",
            "Wet dreamz of the past"
        ],
        "avoid": ["shallow flex bars", "random punchlines"]
    },
    
    "nas": {
        "name": "Nas",
        "icon": "📜",
        "description": "Poetic lyricism, vivid imagery, street narratives",
        "characteristics": {
            "rhyme_density": "high",
            "multisyllabic": True,
            "internal_rhymes": True,
            "storytelling": True,
            "wordplay": "literary",
            "syllables_per_line": (10, 14),
            "vocabulary": "poetic"
        },
        "style_prompt": """Write in Nas's style:
- Use vivid, cinematic imagery
- Tell street narratives with specific details
- Be philosophically deep
- Reference Queensbridge/NYC
- Use literary techniques (similes, metaphors)
- Include references to history and knowledge
- Maintain smooth, laid-back delivery""",
        "example_patterns": [
            "I never sleep, cause sleep is the cousin of death",
            "Life's a bitch and then you die",
            "The world is yours"
        ],
        "avoid": ["rushed delivery", "surface-level content"]
    },
    
    "travis": {
        "name": "Travis Scott",
        "icon": "🎢",
        "description": "Atmospheric, auto-tuned, psychedelic trap",
        "characteristics": {
            "rhyme_density": "low",
            "multisyllabic": False,
            "internal_rhymes": False,
            "storytelling": False,
            "wordplay": "minimal",
            "syllables_per_line": (6, 12),
            "vocabulary": "simple"
        },
        "style_prompt": """Write in Travis Scott's style:
- Use short, punchy phrases
- Focus on vibes and energy over complex lyrics
- Reference drugs, nightlife, and excess
- Include ad-libs (it's lit, straight up, yeah)
- Create atmospheric, spacey imagery
- Reference Houston/Cactus Jack
- Use repetitive, catchy hooks""",
        "example_patterns": [
            "It's lit!",
            "Sicko mode, yeah",
            "Way up, let's go, yeah"
        ],
        "avoid": ["complex rhyme schemes", "long verses"]
    },
    
    "jayz": {
        "name": "Jay-Z",
        "icon": "💎",
        "description": "Business bars, luxury references, clever wordplay",
        "characteristics": {
            "rhyme_density": "medium_high",
            "multisyllabic": True,
            "internal_rhymes": True,
            "storytelling": True,
            "wordplay": "business",
            "syllables_per_line": (10, 16),
            "vocabulary": "sophisticated"
        },
        "style_prompt": """Write in Jay-Z's style:
- Reference business, money, and mogul lifestyle
- Use confident, boss-level delivery
- Include clever double entendres
- Reference Brooklyn/Marcy Projects origin
- Mix hustler mentality with sophistication
- Use metaphors comparing rap to business
- Maintain effortless flow""",
        "example_patterns": [
            "I'm not a businessman, I'm a business, man",
            "Allow me to reintroduce myself",
            "On to the next one"
        ],
        "avoid": ["trying too hard", "overly emotional content"]
    },
    
    "kanye": {
        "name": "Kanye West",
        "icon": "🐻",
        "description": "Innovative, experimental, ego-driven with vulnerability",
        "characteristics": {
            "rhyme_density": "medium",
            "multisyllabic": False,
            "internal_rhymes": True,
            "storytelling": True,
            "wordplay": "creative",
            "syllables_per_line": (8, 14),
            "vocabulary": "eclectic"
        },
        "style_prompt": """Write in Kanye West's style:
- Mix extreme confidence with vulnerability
- Reference fashion, art, and culture
- Be self-aware about ego
- Use unconventional flow patterns
- Include grandiose statements
- Reference Chicago/soul music
- Break the fourth wall""",
        "example_patterns": [
            "I guess we'll never know",
            "New slaves",
            "Runaway from me baby"
        ],
        "avoid": ["conventional structures", "playing it safe"]
    }
}


def get_style(style_key: str) -> Optional[Dict]:
    """Get a single style definition"""
    return ARTIST_STYLES.get(style_key.lower())


def get_all_styles() -> Dict[str, Dict]:
    """Get all available styles"""
    return {
        key: {
            "name": style["name"],
            "icon": style["icon"],
            "description": style["description"]
        }
        for key, style in ARTIST_STYLES.items()
    }


def get_style_prompt(style_key: str) -> str:
    """Get the style prompt for AI generation"""
    style = get_style(style_key)
    if not style:
        return ""
    return style.get("style_prompt", "")


def get_style_context(style_key: str) -> Dict:
    """Get full style context for AI"""
    style = get_style(style_key)
    if not style:
        return {}
    
    return {
        "style_name": style["name"],
        "style_prompt": style.get("style_prompt", ""),
        "characteristics": style.get("characteristics", {}),
        "examples": style.get("example_patterns", []),
        "avoid": style.get("avoid", [])
    }
