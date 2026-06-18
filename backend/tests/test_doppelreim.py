import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.services.rhyme_detector import RhymeDetector
from backend.models import MultisyllabicWord


class TestDoppelreimEngine:
    """Test Doppelreim offline phonetic extraction and search capabilities"""

    def test_extract_english_vowels(self):
        detector = RhymeDetector()
        # "rapper" -> AE1-ER0
        vseq, ekey, count = detector.extract_english_vowels("rapper")
        assert count == 2
        assert "AE1" in vseq
        assert "ER0" in vseq
        assert ekey != ""

        # Test out-of-vocabulary fallback (basic vowel parsing)
        vseq_fallback, ekey_fallback, count_fallback = detector.extract_english_vowels("xyzabc")
        assert count_fallback >= 1

    def test_extract_hindi_vowels(self):
        detector = RhymeDetector()
        # "अपना" -> a-aa
        vseq, ekey, count = detector.extract_hindi_vowels("अपना")
        assert count == 2
        assert vseq == "a-aa"

        # "महान" -> a-aa (final schwa deleted)
        vseq_m, _, count_m = detector.extract_hindi_vowels("महान")
        assert count_m == 2
        assert vseq_m == "a-aa"

    def test_extract_kannada_vowels(self):
        detector = RhymeDetector()
        # "ಬಂಗಾರ" -> a-aa-a
        vseq, ekey, count = detector.extract_kannada_vowels("ಬಂಗಾರ")
        assert count == 3
        assert vseq == "a-aa-a"

        # "ಮಸ್ತಕ" -> a-a-a
        vseq_m, _, count_m = detector.extract_kannada_vowels("ಮಸ್ತಕ")
        assert count_m == 3
        assert vseq_m == "a-a-a"

    @pytest.mark.asyncio
    async def test_dynamic_word_registration(self):
        # We can construct a mock db session or a real in-memory SQLite session
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from backend.database import Base
        
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        async with async_session() as session:
            detector = RhymeDetector()
            
            # Register a word
            await detector.auto_register_word(session, "testword", "en", "EH-AH", "EH-L", 2)
            
            # Check if it was inserted
            query = select(MultisyllabicWord).where(MultisyllabicWord.word == "testword")
            res = await session.execute(query)
            inserted = res.scalar()
            assert inserted is not None
            assert inserted.vowel_sequence == "EH-AH"
            assert inserted.syllable_count == 2
            
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_combinatorial_search(self):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from backend.database import Base
        
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        async with async_session() as session:
            detector = RhymeDetector()
            
            # Pre-populate database with two words
            word1 = MultisyllabicWord(word="next", language="en", syllable_count=1, vowel_sequence="EH", exact_rhyme_key="EH-K-S-T", upvotes=5)
            word2 = MultisyllabicWord(word="level", language="en", syllable_count=2, vowel_sequence="EH-AH", exact_rhyme_key="EH-V-AH-L", upvotes=5)
            session.add_all([word1, word2])
            await session.commit()
            
            # Search for combinatorial rhyme matching sequence "EH-EH-AH" (next + level)
            results = await detector.find_combinatorial_rhymes(session, "EH-EH-AH", "en", allow_slang=True)
            assert len(results) > 0
            assert results[0]["word"] == "next level"
            assert results[0]["syllable_count"] == 3
            
        await engine.dispose()
