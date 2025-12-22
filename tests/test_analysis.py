"""
Tests for analysis modules
"""
import pytest
from app.analysis import SyllableCounter, RhymeDetector, ComplexityScorer, BPMCalculator


class TestSyllableCounter:
    """Tests for syllable counting"""
    
    def test_simple_word(self):
        """Test counting syllables in simple words"""
        counter = SyllableCounter()
        assert counter.count_word_syllables("cat") == 1
        assert counter.count_word_syllables("hello") == 2
        assert counter.count_word_syllables("beautiful") == 3
    
    def test_line_syllables(self):
        """Test counting syllables in a line"""
        counter = SyllableCounter()
        result = counter.count_line_syllables("I am the greatest")
        assert result >= 5  # Approximate
    
    def test_empty_input(self):
        """Test empty input returns 0"""
        counter = SyllableCounter()
        assert counter.count_line_syllables("") == 0
    
    def test_slang_words(self):
        """Test slang/hip-hop vocabulary"""
        counter = SyllableCounter()
        # Should handle slang gracefully
        result = counter.count_line_syllables("ayy bruh we vibin")
        assert result >= 4


class TestRhymeDetector:
    """Tests for rhyme detection"""
    
    def test_perfect_rhyme(self):
        """Test detecting perfect rhymes"""
        detector = RhymeDetector()
        assert detector.words_rhyme("cat", "hat") is True
        assert detector.words_rhyme("flow", "show") is True
        assert detector.words_rhyme("grind", "mind") is True
    
    def test_no_rhyme(self):
        """Test non-rhyming words"""
        detector = RhymeDetector()
        assert detector.words_rhyme("cat", "dog") is False
        assert detector.words_rhyme("love", "hate") is False
    
    def test_internal_rhymes(self):
        """Test detecting internal rhymes"""
        detector = RhymeDetector()
        rhymes = detector.detect_internal_rhymes("I stay on the grind and shine every time")
        assert len(rhymes) > 0
    
    def test_rhyme_scheme(self):
        """Test identifying rhyme scheme"""
        detector = RhymeDetector()
        lines = [
            "I'm making moves in the city",
            "Life is hard but I stay gritty",
            "Chasing dreams every day",
            "Success is just a step away"
        ]
        scheme = detector.get_rhyme_scheme_string(lines)
        assert len(scheme) == 4
        # First two should rhyme (A A), last two should rhyme (B B)
        assert scheme[0] == scheme[1]  # city/gritty
        assert scheme[2] == scheme[3]  # day/away
    
    def test_slant_rhyme(self):
        """Test slant/near rhyme detection"""
        detector = RhymeDetector()
        # These are slant rhymes (similar but not perfect)
        assert detector.words_rhyme("grind", "time", strict=False) is True
        assert detector.words_rhyme("love", "above", strict=False) is True
    
    def test_hip_hop_rhyme_families(self):
        """Test hip-hop specific rhyme families"""
        detector = RhymeDetector()
        # Common hip-hop rhyme patterns - words that share endings
        assert detector._suffix_rhyme("day", "way") is True
        assert detector._suffix_rhyme("flow", "go") is True
        assert detector._suffix_rhyme("night", "fight") is True
        assert detector._suffix_rhyme("nation", "station") is True
    
    def test_clean_punctuation(self):
        """Test words with punctuation are handled"""
        detector = RhymeDetector()
        assert detector.words_rhyme("flow.", "show!") is True
        assert detector.words_rhyme("'bout", "out") is True


class TestComplexityScorer:
    """Tests for complexity scoring"""
    
    def test_simple_line(self):
        """Test scoring a simple line"""
        scorer = ComplexityScorer()
        result = scorer.score_line("I am here", [])
        assert 'overall' in result
        assert 0 <= result['overall'] <= 1
    
    def test_complex_line(self):
        """Test complex multisyllabic line scores higher"""
        scorer = ComplexityScorer()
        simple = scorer.score_line("I am here", [])
        complex_line = scorer.score_line(
            "Contemplating manifestation of my aspirations", []
        )
        assert complex_line['overall'] > simple['overall']
    
    def test_verse_scoring(self):
        """Test scoring a full verse"""
        scorer = ComplexityScorer()
        lines = [
            "Started from the bottom now we here",
            "Grinding every day throughout the year",
            "Vision clear, no fear, persevere"
        ]
        result = scorer.score_verse(lines)
        assert 'overall' in result


class TestBPMCalculator:
    """Tests for BPM calculations"""
    
    def test_syllable_target(self):
        """Test getting syllable targets for different BPMs"""
        calc = BPMCalculator()
        
        slow = calc.get_syllable_target(80)
        fast = calc.get_syllable_target(160)
        
        assert slow['optimal'] < fast['optimal']
    
    def test_flow_styles(self):
        """Test recommended flow styles"""
        calc = BPMCalculator()
        
        result = calc.suggest_flow_style(140)
        assert 'recommended_styles' in result
        assert len(result['recommended_styles']) > 0
    
    def test_bar_timing(self):
        """Test bar timing analysis"""
        calc = BPMCalculator()
        result = calc.analyze_bar_timing("Eight syllable line here", 140)
        assert 'syllables' in result
        assert 'fits_beat' in result


class TestRhymeDictionary:
    """Tests for rhyme dictionary"""
    
    def test_find_rhymes(self):
        """Test finding rhymes for a word"""
        from app.analysis import RhymeDictionary
        dictionary = RhymeDictionary()
        rhymes = dictionary.find_rhymes("cat")
        assert len(rhymes) > 0
        assert all(isinstance(r, str) for r in rhymes)
    
    def test_get_rhyme_info(self):
        """Test getting rhyme info"""
        from app.analysis import RhymeDictionary
        dictionary = RhymeDictionary()
        info = dictionary.get_rhyme_info("flow")
        assert 'word' in info
        assert 'syllables' in info
        assert 'exact_rhymes' in info
    
    def test_slang_categories(self):
        """Test hip-hop slang categories"""
        from app.analysis import RhymeDictionary
        dictionary = RhymeDictionary()
        categories = dictionary.get_all_categories()
        assert 'money' in categories
        assert 'friends' in categories
    
    def test_get_synonyms(self):
        """Test getting slang synonyms"""
        from app.analysis import RhymeDictionary
        dictionary = RhymeDictionary()
        synonyms = dictionary.get_synonyms("money")
        assert 'bread' in synonyms or 'paper' in synonyms
    
    def test_suggest_rhyme_words(self):
        """Test suggesting rhymes for a line"""
        from app.analysis import RhymeDictionary
        dictionary = RhymeDictionary()
        suggestions = dictionary.suggest_rhyme_words("I'm on the grind")
        assert isinstance(suggestions, dict)

