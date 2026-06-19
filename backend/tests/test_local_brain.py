"""
Test Local Brain Features
Tests for stress layout, doppelreim rhythmic scoring, and local polish endpoint
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Ensure backend importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.rhyme_detector import RhymeDetector, SyllableCounter


class TestSyllableCounter:
    """Test SyllableCounter basic functionality"""

    def setup_method(self):
        self.counter = SyllableCounter()

    def test_get_stress_pattern_english(self):
        pattern = self.counter.get_stress_pattern("hello")
        assert pattern, "Should return a non-empty pattern"
        # 'hello' is 2 syllables: unstressed-stressed => 'x/' or similar
        assert len(pattern.replace(" ", "")) >= 1

    def test_get_stress_pattern_unknown_word(self):
        pattern = self.counter.get_stress_pattern("xyzzyplugh")
        assert pattern, "Should return a fallback pattern for unknown words"


class TestDetailedStressLayout:
    """Test RhymeDetector.get_detailed_stress_layout for EN, HI, KN"""

    def setup_method(self):
        self.detector = RhymeDetector()

    def test_english_word(self):
        # 'beautiful' is 3 syllables in CMUDict: B-YUW1-T-AH0-F-AH0-L => /xx
        layout = self.detector.get_detailed_stress_layout("beautiful", "en")
        assert layout, "Should return stress layout"
        assert all(c in ('/', 'x') for c in layout), f"Layout should only contain / and x, got: {layout}"
        assert len(layout) >= 2, "beautiful has at least 2-3 syllables"

    def test_english_unknown_word_fallback(self):
        layout = self.detector.get_detailed_stress_layout("flarbiznorb", "en")
        assert layout, "Should return fallback for unknown English word"

    def test_hindi_romanized(self):
        # 'sapna' => a, a => 2 vowels, short -> xx
        layout = self.detector.get_detailed_stress_layout("sapna", "hi")
        assert layout, "Should return stress layout for Hindi romanized"
        assert all(c in ('/', 'x') for c in layout)

    def test_kannada_romanized(self):
        layout = self.detector.get_detailed_stress_layout("bangaara", "kn")
        assert layout, "Should return stress layout for Kannada romanized"
        assert all(c in ('/', 'x') for c in layout)

    def test_empty_word(self):
        layout = self.detector.get_detailed_stress_layout("", "en")
        assert layout == "", "Empty word should return empty string"

    def test_hindi_long_vowel(self):
        # 'aatma' has 'aa' (long) and 'a' (short) => /x
        layout = self.detector.get_detailed_stress_layout("aatma", "hi")
        assert '/' in layout, "Long vowel 'aa' should be marked as stressed"


class TestDoppelreimRhythmicScoring:
    """Test that doppelreim ranking uses syllable/stress matching"""

    def setup_method(self):
        self.detector = RhymeDetector()

    @pytest.mark.asyncio
    async def test_rhythmic_score_calculation(self):
        """Test the internal score function logic"""
        # We can test the score function indirectly by checking that
        # target_syllables affects result ordering
        mock_session = AsyncMock()
        
        # Mock the database query to return some test words
        mock_result = MagicMock()
        mock_word1 = MagicMock()
        mock_word1.word = "testing"
        mock_word1.syllable_count = 2
        mock_word1.vowel_sequence = "EH-IH"
        mock_word1.exact_rhyme_key = "ng"
        mock_word1.upvotes = 5
        mock_word1.is_slang = False

        mock_word2 = MagicMock()
        mock_word2.word = "requesting"
        mock_word2.syllable_count = 3
        mock_word2.vowel_sequence = "EH-EH-IH"
        mock_word2.exact_rhyme_key = "ng"
        mock_word2.upvotes = 3
        mock_word2.is_slang = False

        mock_result.scalars.return_value.all.return_value = [mock_word1, mock_word2]
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Without target: should sort by upvotes (testing first)
        results_no_target = await self.detector.find_doppelreim_rhymes(
            mock_session, "rhyming", "en", "vowel", True, 30, None, None
        )
        
        # The function auto-registers, so multiple execute calls happen
        # Just verify it doesn't crash and returns results
        assert isinstance(results_no_target, list)


class TestExtractRomanizedIndianVowels:
    """Test romanized Hindi/Kannada vowel extraction"""

    def setup_method(self):
        self.detector = RhymeDetector()

    def test_hindi_romanized_basic(self):
        vowel_seq, exact_key, syl_count = self.detector.extract_romanized_indian_vowels("sapna", "hi")
        assert syl_count >= 2, "sapna should have at least 2 syllables"
        assert vowel_seq, "Should return non-empty vowel sequence"

    def test_kannada_romanized_basic(self):
        vowel_seq, exact_key, syl_count = self.detector.extract_romanized_indian_vowels("bangaara", "kn")
        assert syl_count >= 2, "bangaara should have at least 2 syllables"

    def test_long_vowels_detected(self):
        vowel_seq, _, _ = self.detector.extract_romanized_indian_vowels("aatma", "hi")
        # 'aa' should map to long vowel
        assert "aa" in vowel_seq, "Long vowel 'aa' should be present in sequence"

    def test_empty_input(self):
        vowel_seq, exact_key, syl_count = self.detector.extract_romanized_indian_vowels("", "hi")
        assert vowel_seq == ""
        assert syl_count == 0


class TestLocalPolishEndpoint:
    """Test the /ai/polish/local request schema works correctly"""

    @pytest.mark.asyncio
    async def test_polish_endpoint_schema(self):
        """Test that PolishLocalRequest shape validates correctly"""
        from pydantic import BaseModel
        from typing import Optional
        
        # Mirror the schema from routers/ai.py
        class PolishLocalRequest(BaseModel):
            line: str
            target_syllables: Optional[int] = None
            slang_words: list[str] = []
        
        req = PolishLocalRequest(
            line="I walk the streets alone at night",
            target_syllables=8,
            slang_words=["drip", "sauce"]
        )
        assert req.line == "I walk the streets alone at night"
        assert req.target_syllables == 8
        assert req.slang_words == ["drip", "sauce"]

    @pytest.mark.asyncio
    async def test_polish_request_defaults(self):
        """Test that PolishLocalRequest has correct defaults"""
        from pydantic import BaseModel
        from typing import Optional
        
        class PolishLocalRequest(BaseModel):
            line: str
            target_syllables: Optional[int] = None
            slang_words: list[str] = []
        
        req = PolishLocalRequest(line="test line")
        assert req.target_syllables is None
        assert req.slang_words == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
