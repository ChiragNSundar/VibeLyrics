"""
Flow Pattern Templates Service
Pre-built rhythmic patterns for different lyrical styles
"""

FLOW_PATTERNS = {
    "triplet": {
        "name": "Triplet Flow",
        "description": "Groups of 3 syllables per beat — bouncy, Migos-style.",
        "syllable_target": 12,
        "stress_pattern": "daDAdaDAdaDA",
        "example": "Runnin' it up / flippin' the cup / livin' it up",
        "bpm_range": [120, 160],
    },
    "double_time": {
        "name": "Double Time",
        "description": "Twice the normal syllables per bar — rapid-fire, Tech N9ne style.",
        "syllable_target": 16,
        "stress_pattern": "dadaDAdadaDAdadaDA",
        "example": "Everybody wanna talk about the money and the fame",
        "bpm_range": [80, 110],
    },
    "halftime": {
        "name": "Halftime",
        "description": "Half the syllables, drawn out delivery — J. Cole, Nipsey style.",
        "syllable_target": 6,
        "stress_pattern": "DA da DA da DA da",
        "example": "I been through the storm",
        "bpm_range": [130, 170],
    },
    "boom_bap": {
        "name": "Boom Bap",
        "description": "Classic hip-hop rhythm — Nas, Jay-Z style. Emphasis on 2nd and 4th beat.",
        "syllable_target": 10,
        "stress_pattern": "da DA da da DA da da DA da DA",
        "example": "I got the city on my back, no question",
        "bpm_range": [85, 100],
    },
    "trap_bounce": {
        "name": "Trap Bounce",
        "description": "Bouncy hi-hat rhythm with short punchy lines — Future, Young Thug style.",
        "syllable_target": 8,
        "stress_pattern": "DA da DA da DA da DA da",
        "example": "Drip too hard, yeah",
        "bpm_range": [130, 150],
    },
    "spoken_word": {
        "name": "Spoken Word",
        "description": "Free-form, emphasis on storytelling — Kendrick, Lupe style.",
        "syllable_target": 14,
        "stress_pattern": "free",
        "example": "I remember when I used to sit up in the kitchen at night",
        "bpm_range": [70, 95],
    },
}


def get_flow_template(name: str):
    """Get a specific flow template by name."""
    return FLOW_PATTERNS.get(name)


def list_flow_templates():
    """Get all available flow templates."""
    return [
        {"id": key, **value}
        for key, value in FLOW_PATTERNS.items()
    ]
