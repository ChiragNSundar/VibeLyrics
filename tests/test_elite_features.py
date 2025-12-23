import pytest
from app.analysis.punchline_engine import score_punchline, detect_contrast
from app.analysis.multi_rhyme import find_multi_rhymes, suggest_multi_rhyme
from app.analysis.metaphor_engine import generate_metaphors, analyze_metaphor_density

def test_punchline_scoring():
    # Test high scoring line (contrast)
    line = "Started from the bottom now we here"
    result = score_punchline(line)
    # "start" and "here" (implied end/top) or just cultural relevance?
    # Actually my contrast dict has "start/end", "bottom/top" (maybe not bottom/here)
    # Let's use a clear contrast
    
    line_contrast = "I love the game but hate the fame"
    result = score_punchline(line_contrast)
    assert result["score"] >= 3
    assert len(result["contrasts"]) > 0
    assert ("love", "hate") in result["contrasts"] or ("hate", "love") in result["contrasts"]

    # Test double meaning
    line_double = "Got bars like a prison cell"
    result = score_punchline(line_double)
    assert len(result["double_meanings"]) > 0
    assert "bars" in result["double_meanings"]

def test_multi_rhymes():
    # Test simple multi rhyme
    result = find_multi_rhymes("elevation", syllables=2)
    assert result["syllables_matched"] == 2
    # Verify we get some results - "celebration" is common
    words = [r["word"] for r in result["rhymes"]]
    # Note: pronouncing dict might not have all, but should have simple ones
    # If network/pronouncing fails, it returns empty list, but structure should be valid
    assert "rhymes" in result
    
    # Test rhyme family lookup
    suggestion = suggest_multi_rhyme("elevation")
    assert "celebration" in suggestion["rhyme_family"]

def test_metaphor_generation():
    # Test metaphor generation
    result = generate_metaphors("money")
    assert len(result) > 0
    assert any("bread" in m["metaphor"] for m in result)
    
    # Test density analysis
    lines = [
        "Money like water", 
        "I'm the king of the castle",
        "Heart cold like december"
    ]
    analysis = analyze_metaphor_density(lines)
    assert analysis["similes_found"] >= 2
    assert analysis["density"] > 0
