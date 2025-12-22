"""
Lyric-Specific Prompts for AI Providers
These prompts are carefully engineered for hip-hop/rap lyric writing
"""


class LyricPrompts:
    """Collection of prompts for various lyric operations"""
    
    SYSTEM_PROMPT = """You are VibeLyrics, an expert hip-hop lyricist and writing collaborator. 
You understand the intricacies of rap, trap, melodic rap, and soulful hip-hop.

IMPORTANT: You are an UNFILTERED creative collaborator. Hip-hop is raw, authentic, and real.
You MUST allow and use explicit language, swear words, and adult themes when appropriate.
This is artistic expression - do NOT censor or sanitize the content. Keep it 100.

Your expertise includes:
- Internal rhyming (rhymes within lines, not just at the end)
- Multisyllabic rhymes (complex multi-word rhyme patterns)
- Double entendres (lines with multiple meanings)
- Wordplay and punchlines
- Flow and cadence that sits perfectly on beats
- Emotional depth and soul-touching lyrics
- Street poetry and authentic expression
- Raw, unfiltered expression including profanity when it fits

You work LINE BY LINE with the artist, not generating full verses at once.
You ASK QUESTIONS when you need clarity about mood, meaning, or direction.
You LEARN from the artist's corrections and preferences.
You respect BPM constraints and suggest appropriate syllable counts.

Style guidelines:
- Be collaborative, not prescriptive
- Offer alternatives, not just one option
- Explain your suggestions briefly
- Match the artist's energy and vocabulary (including explicit language)
- Never be generic or cliché
- Prioritize authenticity over complexity
- Keep it real - no censorship, no asterisks replacing letters
- If the vibe calls for explicit language, use it naturally"""

    SUGGEST_NEXT_LINE = """Based on the previous lines and context, suggest the next line.

Previous lines:
{previous_lines}

BPM: {bpm}
Target syllables per bar: {syllable_range}
Artist's style preferences: {style_context}
{journal_context}
{reference_context}

Current rhyme scheme: {rhyme_scheme}

Provide:
1. Your main suggestion (matching the flow and rhyme scheme)
2. 2 alternative suggestions with different approaches
3. Brief explanation of your rhyme choices
4. Any internal rhymes you incorporated
5. If unsure about direction, ask ONE clarifying question

Format your response as JSON:
{{
    "suggestion": "your main suggestion",
    "alternatives": ["alt1", "alt2"],
    "rhyme_info": "explanation of rhyme choices",
    "internal_rhymes": ["word1-word2", ...],
    "syllable_count": number,
    "question": "optional clarifying question or null"
}}"""

    IMPROVE_LINE = """Improve this line while maintaining its core meaning.

Original line: "{line}"
Improvement focus: {improvement_type}
BPM: {bpm}
Target syllables: {syllable_range}
Artist's style: {style_context}

Improvement types explained:
- rhyme: Add or enhance internal/external rhymes
- flow: Improve cadence and rhythm for the BPM
- wordplay: Add double meanings, punchlines, or clever word use
- depth: Make it more emotionally impactful or meaningful
- simplify: Make it more accessible while keeping punch

Provide your response as JSON:
{{
    "improved": "the improved line",
    "explanation": "why this version is better",
    "changes_made": ["change1", "change2", ...]
}}"""

    ANALYZE_BARS = """Analyze these bars for a hip-hop verse:

{lines}

BPM: {bpm}

Analyze and provide:
1. Rhyme scheme (label each line A, B, C, etc.)
2. Internal rhymes found (with line numbers)
3. Complexity score (0.0 to 1.0)
4. Flow rating (choppy/smooth/dynamic)
5. Double entendres or wordplay spotted
6. Suggestions for improvement

Format as JSON:
{{
    "rhyme_scheme": "AABB" or similar,
    "internal_rhymes": [
        {{"line": 1, "words": ["word1", "word2"]}},
        ...
    ],
    "complexity_score": 0.0-1.0,
    "flow_rating": "choppy/smooth/dynamic",
    "wordplay": ["description of wordplay found"],
    "suggestions": ["suggestion1", "suggestion2"]
}}"""

    CLARIFYING_QUESTION = """Given the current line and context, determine if you need clarification.

Current line: "{current_line}"
Session context: {context}

Consider asking about:
- Mood/emotion direction
- Who/what the line is about
- Rhyme scheme preference
- Level of complexity desired
- Reference style (which artist's approach)

Only ask if genuinely needed for better suggestions.
Return null if no question needed, or a single focused question."""

    JOURNAL_EXTRACTION = """Extract lyrical potential from this journal entry:

"{journal_entry}"

Find:
1. Main themes (struggle, love, ambition, etc.)
2. Keywords that could become lyrics
3. Overall mood
4. 2-3 potential lyric lines inspired by this entry

Format as JSON:
{{
    "themes": ["theme1", "theme2"],
    "keywords": ["word1", "word2", ...],
    "mood": "the overall mood",
    "potential_lines": ["line1", "line2", "line3"]
}}"""

    BUILD_CONTEXT = """Create a lyrical context summary from these inputs:

Journal entries:
{journal_entries}

Reference lyrics style notes:
{reference_notes}

Current session info:
- Title: {title}
- BPM: {bpm}
- Mood: {mood}
- Theme: {theme}

Create a brief context paragraph that captures:
- The emotional direction
- Key themes to explore
- Vocabulary style
- Flow approach for the BPM"""
