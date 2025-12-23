"""
Tests for performance optimizations:
- Singleton RhymeDictionary
- Async BPM Detection
"""
import pytest
import threading
import time


class TestRhymeDictionarySingleton:
    """Tests for the Singleton pattern on RhymeDictionary."""

    def test_singleton_returns_same_instance(self):
        """Verify get_rhyme_dictionary() always returns the same object."""
        from app.analysis import get_rhyme_dictionary
        
        dict1 = get_rhyme_dictionary()
        dict2 = get_rhyme_dictionary()
        
        assert dict1 is dict2

    def test_singleton_cache_persists(self):
        """Verify the cache is shared across calls via the singleton."""
        from app.analysis import get_rhyme_dictionary
        
        dictionary = get_rhyme_dictionary()
        
        # Perform a lookup to populate the cache
        word = "test_singleton_word_xyz"
        # We use find_rhymes which populates self.cache
        # Even if no rhymes are found, the key should be in cache
        dictionary.find_rhymes(word)
        
        assert word in dictionary.cache

        # Get the "new" instance and check if it has the same cache
        dict2 = get_rhyme_dictionary()
        assert word in dict2.cache


class TestAsyncBPMDetection:
    """Tests for the non-blocking async BPM detection."""

    def test_upload_audio_returns_immediately(self, client, sample_session, monkeypatch):
        """
        The /upload_audio endpoint should return quickly without waiting
        for BPM detection to complete.
        """
        import io
        import sys
        from unittest.mock import MagicMock
        
        # Create a mock module for audio_analyzer that simulates a slow detect_bpm
        mock_audio_module = MagicMock()
        def slow_detect_bpm(path):
            time.sleep(5)  # Simulate slow processing
            return 120
        mock_audio_module.detect_bpm = slow_detect_bpm
        
        # Inject the mock into sys.modules BEFORE the thread imports it
        monkeypatch.setitem(sys.modules, 'app.analysis.audio_analyzer', mock_audio_module)
        
        # Create a simple fake audio file
        fake_audio = (io.BytesIO(b"fake audio data"), "test.mp3")
        
        start_time = time.time()
        response = client.post(
            f'/session/{sample_session}/upload_audio',
            data={'audio_file': fake_audio},
            content_type='multipart/form-data'
        )
        elapsed_time = time.time() - start_time
        
        # The request should return almost immediately (less than 2 seconds)
        # because the BPM detection happens in a background thread.
        assert elapsed_time < 2.0, f"Request took {elapsed_time:.2f}s, should be \u003c 2s"
        
        # The response should indicate success
        data = response.get_json()
        assert data.get('success') is True
        assert 'message' in data

