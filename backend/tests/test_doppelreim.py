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

    @pytest.mark.asyncio
    async def test_combinatorial_search_three_words(self):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from backend.database import Base
        
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        async with async_session() as session:
            detector = RhymeDetector()
            
            # Pre-populate database with words for a 3-word combo
            # "EH-EH-AH-OW" -> "next" (EH) + "level" (EH-AH) + "go" (OW)
            word1 = MultisyllabicWord(word="next", language="en", syllable_count=1, vowel_sequence="EH", exact_rhyme_key="EH-K-S-T", upvotes=5)
            word2 = MultisyllabicWord(word="level", language="en", syllable_count=2, vowel_sequence="EH-AH", exact_rhyme_key="EH-V-AH-L", upvotes=5)
            word3 = MultisyllabicWord(word="go", language="en", syllable_count=1, vowel_sequence="OW", exact_rhyme_key="OW", upvotes=5)
            session.add_all([word1, word2, word3])
            await session.commit()
            
            results = await detector.find_combinatorial_rhymes(session, "EH-EH-AH-OW", "en", allow_slang=True)
            assert len(results) > 0
            assert results[0]["word"] == "next level go"
            assert results[0]["syllable_count"] == 4
            
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_cross_language_syllable_filtering(self):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from backend.database import Base
        
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        async with async_session() as session:
            detector = RhymeDetector()
            
            # Extract source IPA dynamically to be environment-agnostic (CMUDict vs fallback)
            src_vowels, _, src_syls = detector.extract_vowels("fire", "en")
            src_ipa = detector._normalize_to_ipa_key(src_vowels, "en")
            
            src_parts = src_ipa.split("-")
            near_ipa = "-".join(src_parts[:-1] + ["near"]) if src_parts else "near"
            
            # Target words:
            # 1. Hindi "shaayar" (syllable_count same, exact matching ipa_key) -> exact match
            # 2. Hindi "nearmatch" (syllable_count same, near matching ipa_key) -> near match (distance 1)
            # 3. Hindi "bahut-bada" (syllable_count + 2, different ipa_key) -> out of syllable range (+/-1)
            
            w1 = MultisyllabicWord(word="shaayar", language="hi", syllable_count=src_syls, vowel_sequence="i-e", exact_rhyme_key="ar", upvotes=5, ipa_key=src_ipa)
            w2 = MultisyllabicWord(word="nearmatch", language="hi", syllable_count=src_syls, vowel_sequence="i-a", exact_rhyme_key="ch", upvotes=5, ipa_key=near_ipa)
            w3 = MultisyllabicWord(word="bahut-bada", language="hi", syllable_count=src_syls + 2, vowel_sequence="a-u-a-aa", exact_rhyme_key="aa", upvotes=5, ipa_key="ʌ-ʊ-ʌ-aː")
            session.add_all([w1, w2, w3])
            await session.commit()
            
            results = await detector.find_cross_language_rhymes(session, "fire", source_lang="en", target_lang="hi")
            
            words = [r["word"] for r in results]
            assert "shaayar" in words
            assert "nearmatch" in words
            # Should NOT match bahut-bada (too many syllables)
            assert "bahut-bada" not in words

        await engine.dispose()
