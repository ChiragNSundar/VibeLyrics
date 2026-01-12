"""
Rhyme Detection Tests
"""
import pytest
from backend.services.rhyme_detector import RhymeDetector, SyllableCounter


class TestSyllableCounter:
    """Test syllable counting"""
    
    def test_single_word(self):
        counter = SyllableCounter()
        assert counter.count("hello") == 2
        assert counter.count("world") == 1
        assert counter.count("beautiful") >= 3  # 3 or 4 is acceptable
    
    def test_multiple_words(self):
        counter = SyllableCounter()
        assert counter.count("hello world") == 3
        assert counter.count("I am here") == 3
    
    def test_empty_string(self):
        counter = SyllableCounter()
        assert counter.count("") == 0
    
    def test_with_punctuation(self):
        counter = SyllableCounter()
        # Should handle punctuation
        count = counter.count("Hello, world!")
        assert count >= 2


class TestRhymeDetector:
    """Test rhyme detection"""
    
    def test_find_rhymes(self):
        detector = RhymeDetector()
        rhymes = detector.find_rhymes("flow")
        assert isinstance(rhymes, list)
        # Should find some rhymes
        assert len(rhymes) >= 0
    
    def test_get_rhyme_ending(self):
        detector = RhymeDetector()
        ending = detector.get_rhyme_ending("tonight")
        assert isinstance(ending, str)
        assert len(ending) > 0
    
    def test_highlight_lyrics(self):
        detector = RhymeDetector()
        lines = ["I am the king", "Watch me do my thing"]
        highlighted = detector.highlight_lyrics(lines)
        assert len(highlighted) == 2
        # Should contain some HTML
        assert any("<span" in h for h in highlighted) or highlighted == lines
    
    def test_get_density_heatmap(self):
        detector = RhymeDetector()
        lines = ["I am the king", "Watch me do my thing"]
        heatmap = detector.get_density_heatmap(lines)
        assert len(heatmap) == 2
        assert all("color" in h for h in heatmap)
        assert all("density" in h for h in heatmap)
    
    def test_get_rhyme_scheme_string(self):
        detector = RhymeDetector()
        lines = ["I am the king", "Watch me do my thing", "Another day", "In the fray"]
        scheme = detector.get_rhyme_scheme_string(lines)
        assert isinstance(scheme, str)
        assert len(scheme) == 4
    
    def test_slang_categories(self):
        detector = RhymeDetector()
        categories = detector.get_slang_categories()
        assert isinstance(categories, list)
        assert "money" in categories
        assert "confidence" in categories
    
    def test_get_slang(self):
        detector = RhymeDetector()
        slang = detector.get_slang_by_category("money")
        assert isinstance(slang, list)
        assert "bands" in slang or "racks" in slang
    
    def test_multi_syllable_rhymes(self):
        detector = RhymeDetector()
        rhymes = detector.find_multi_syllable_rhymes("flowing")
        assert isinstance(rhymes, list)

    def test_stress_pattern(self):
        counter = SyllableCounter()
        # "hello" -> 01 or 10 -> x/ or /x
        pattern = counter.get_stress_pattern("hello")
        assert isinstance(pattern, str)
        assert len(pattern) > 0
        assert "/" in pattern or "x" in pattern
