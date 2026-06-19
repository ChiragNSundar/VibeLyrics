"""
Rhyme Detection Service
Ported from Flask app with CMU dictionary and Indian language support
"""
import pronouncing
import re
from typing import List, Dict, Optional
from collections import OrderedDict
from .syllable_utils import count_syllables as _shared_count_syllables
from functools import lru_cache
from sqlalchemy import select, func, insert
from sqlalchemy.ext.asyncio import AsyncSession
try:
    from ..models import MultisyllabicWord, RhymeFeedback
except (ImportError, ValueError):
    from backend.models import MultisyllabicWord, RhymeFeedback


class SyllableCounter:
    """Count syllables in text"""
    
    def count(self, text: str) -> int:
        """Count syllables in text (delegates to shared utility)"""
        words = text.lower().split()
        total = 0
        for word in words:
            word = re.sub(r'[^a-z]', '', word)
            if not word:
                continue
            total += _shared_count_syllables(word)
        return total

    def get_stress_pattern(self, text: str) -> str:
        """Get stress pattern (1=primary, 2=secondary, 0=unstressed)"""
        words = text.lower().split()
        pattern = []
        
        for word in words:
            word = re.sub(r'[^a-z]', '', word)
            if not word:
                continue
                
            phones = pronouncing.phones_for_word(word)
            if phones:
                # Get first pronunciation's stresses
                stress = pronouncing.stresses(phones[0])
                # Convert to simple representation (x=unstressed, /=stressed)
                simple = stress.replace('1', '/').replace('2', '/').replace('0', 'x')
                pattern.append(simple)
            else:
                # Guess based on length (simplified)
                length = len(re.findall(r'[aeiouy]+', word))
                pattern.append('x' * max(1, length))
        
        return " ".join(pattern)


class RhymeDetector:
    """Detect rhymes with multi-language support"""
    
    # Hip-hop rhyme families
    RHYME_FAMILIES = [
        ['ow', 'oh', 'o', 'oe'],
        ['ay', 'ey', 'ai', 'ei'],
        ['ee', 'ea', 'ie', 'y'],
        ['oo', 'ue', 'ew', 'ou'],
        ['ar', 'ah', 'a'],
        ['er', 'ir', 'ur'],
        ['in', 'en', 'an'],
        ['ight', 'ite', 'yte'],
        ['ack', 'ak', 'ac'],
        ['ame', 'aim', 'aym'],
    ]
    
    # Indian language rhyme families (Hindi/Kannada)
    INDIAN_FAMILIES = [
        ['aa', 'a'],
        ['ee', 'i', 'ii'],
        ['oo', 'u', 'uu'],
        ['ai', 'ay', 'ae', 'ey'],
        ['au', 'aw', 'ao', 'ow'],
        ['odu', 'edu', 'idu', 'adu', 'udu'],
        ['ona', 'ena', 'ina', 'ana', 'una'],
        ['ali', 'eli', 'ili', 'oli', 'uli'],
        ['ana', 'ena', 'ina', 'ona', 'una'],
        ['ata', 'eta', 'ita', 'ota', 'uta'],
    ]
    
    # Slang categories
    SLANG = {
        "money": ["bands", "racks", "stacks", "guap", "cheese", "bread", "cheddar", "paper"],
        "success": ["winning", "bossin", "shining", "grinding", "hustling"],
        "confidence": ["drip", "sauce", "swag", "fly", "icy", "cold"],
        "negative": ["cap", "fake", "lame", "wack", "trash"],
    }
    
    romanized_words_map: Dict[str, str] = {}
    
    def __init__(self):
        self.syllable_counter = SyllableCounter()
        self._cache = OrderedDict()
        self._cache_max_size = 500

    def clear_cache(self):
        """Clear the in-memory lookup cache"""
        self._cache.clear()

    def extract_vowels(self, word: str, language: str) -> tuple:
        """Extract vowel sequence, exact rhyme key, and syllable count based on language and script type"""
        word = word.strip()
        if not word:
            return "", "", 0
            
        if language == 'en':
            return self.extract_english_vowels(word)
        elif language == 'hi':
            if re.search(r'[\u0900-\u097f]', word):
                return self.extract_hindi_vowels(word)
            else:
                return self.extract_romanized_indian_vowels(word, 'hi')
        elif language == 'kn':
            if re.search(r'[\u0c80-\u0cff]', word):
                return self.extract_kannada_vowels(word)
            else:
                return self.extract_romanized_indian_vowels(word, 'kn')
        else:
            # Fallback to English-like vowel groups
            vowels = re.findall(r'[aeiouy]+', word.lower())
            vowel_seq = "-".join([v.upper() for v in vowels])
            exact_key = word[-2:] if len(word) >= 2 else word
            return vowel_seq, exact_key, max(1, len(vowels))

    def extract_english_vowels(self, word: str) -> tuple:
        """Extract vowel sequence and exact rhyme key for English using CMUDict"""
        word_clean = re.sub(r'[^a-z]', '', word.lower())
        if not word_clean:
            return "", "", 0
        
        phones_list = pronouncing.phones_for_word(word_clean)
        if not phones_list:
            vowels = re.findall(r'[aeiouy]+', word_clean)
            vowel_seq = "-".join([v.upper() for v in vowels])
            exact_key = word_clean[-2:] if len(word_clean) >= 2 else word_clean
            return vowel_seq, exact_key, max(1, len(vowels))
            
        phones = phones_list[0]
        vowel_parts = []
        for p in phones.split():
            if p[-1].isdigit():
                vowel_parts.append(p)
                
        vowel_seq = "-".join(vowel_parts)
        exact_key = pronouncing.rhyming_part(phones) or ""
        syllable_count = pronouncing.syllable_count(phones)
        
        return vowel_seq, exact_key, syllable_count

    def extract_hindi_vowels(self, word: str) -> tuple:
        """Extract vowel sequence and exact rhyme key for Hindi Devanagari script"""
        vowels = []
        n = len(word)
        i = 0
        
        # Swara mapping (Independent Vowels)
        swara_map = {
            'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ii', 'उ': 'u', 'ऊ': 'uu',
            'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au'
        }
        # Matra mapping (Dependent Vowel Signs)
        matra_map = {
            'ा': 'aa', 'ि': 'i', 'ी': 'ii', 'ु': 'u', 'ू': 'uu',
            'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ृ': 'ri'
        }
        
        while i < n:
            char = word[i]
            code = ord(char)
            
            if char in swara_map:
                vowels.append(swara_map[char])
                i += 1
            # Check if Devanagari consonant (Standard range 0x0915 to 0x0939, additional glyphs like क़)
            elif (0x0915 <= code <= 0x0939) or (0x0958 <= code <= 0x095F) or char == 'ळ':
                next_char = word[i+1] if i + 1 < n else None
                if next_char and next_char in matra_map:
                    vowels.append(matra_map[next_char])
                    i += 2
                elif next_char == '्':
                    # Halant kills the inherent vowel
                    i += 2
                else:
                    # Inherent schwa 'a'. Apply schwa deletion rules.
                    has_schwa = True
                    
                    # 1. Final schwa deletion
                    if i == n - 1 and len(vowels) > 0:
                        has_schwa = False
                    # 2. Intermediate schwa deletion (if not first syllable, and followed by consonant + matra)
                    elif len(vowels) > 0 and i + 2 < n:
                        next_next_char = word[i+2]
                        is_next_consonant = next_char is not None and (
                            (0x0915 <= ord(next_char) <= 0x0939) or
                            (0x0958 <= ord(next_char) <= 0x095F) or
                            next_char == 'ळ'
                        )
                        is_next_next_matra = next_next_char in matra_map
                        if is_next_consonant and is_next_next_matra:
                            has_schwa = False
                            
                    if has_schwa:
                        vowels.append('a')
                    i += 1
            else:
                i += 1
                
        if not vowels:
            vowels = ['a']
            
        vowel_seq = "-".join(vowels)
        exact_key = word[-2:] if len(word) >= 2 else word
        return vowel_seq, exact_key, len(vowels)

    def extract_kannada_vowels(self, word: str) -> tuple:
        """Extract vowel sequence and exact rhyme key for Kannada script"""
        vowels = []
        n = len(word)
        i = 0
        
        swara_map = {
            'ಅ': 'a', 'ಆ': 'aa', 'ಇ': 'i', 'ಈ': 'ii', 'ಉ': 'u', 'ಊ': 'uu',
            'ಎ': 'e', 'ಏ': 'ee', 'ಐ': 'ai', 'ಒ': 'o', 'ಓ': 'oo', 'ಔ': 'au', 'ಋ': 'ri'
        }
        matra_map = {
            'ಾ': 'aa', 'i': 'i', 'ೀ': 'ii', 'ು': 'u', 'ೂ': 'uu',
            'ೆ': 'e', 'ೇ': 'ee', 'ೈ': 'ai', 'ೊ': 'o', 'ೋ': 'oo', 'ೌ': 'au', 'ೃ': 'ri'
        }
        # Add support for standard Kannada matra 'ಿ' (which is different from latin 'i')
        matra_map['ಿ'] = 'i'
        
        while i < n:
            char = word[i]
            code = ord(char)
            
            if char in swara_map:
                vowels.append(swara_map[char])
                i += 1
            # Check if Kannada consonant (Standard range 0x0C95 to 0x0CB9, and ಳ 0x0CDE)
            elif (0x0C95 <= code <= 0x0CB9) or code == 0x0CDE:
                next_char = word[i+1] if i + 1 < n else None
                if next_char and next_char in matra_map:
                    vowels.append(matra_map[next_char])
                    i += 2
                elif next_char == '್':
                    i += 2
                else:
                    vowels.append('a')
                    i += 1
            else:
                i += 1
                
        if not vowels:
            vowels = ['a']
            
        vowel_seq = "-".join(vowels)
        exact_key = word[-2:] if len(word) >= 2 else word
        return vowel_seq, exact_key, len(vowels)

    def extract_romanized_indian_vowels(self, word: str, language: str) -> tuple:
        """Extract vowel sequence, exact rhyme key, and syllable count for Romanized Hindi/Kannada"""
        word_clean = re.sub(r'[^a-z]', '', word.lower())
        if not word_clean:
            return "", "", 0
            
        vowel_pattern = re.compile(r'(aa|ee|ii|oo|uu|ai|au|ae|ou|a|e|i|o|u|y)')
        matches = vowel_pattern.findall(word_clean)
        
        if not matches:
            return "a", word_clean[-2:] if len(word_clean) >= 2 else word_clean, 1
            
        phonetic_vowels = []
        for idx, m in enumerate(matches):
            is_final = (idx == len(matches) - 1)
            if m in ('aa', 'ae'):
                phonetic_vowels.append('aa')
            elif m in ('ee', 'ii'):
                phonetic_vowels.append('ii' if language == 'hi' else 'ee')
            elif m in ('oo', 'uu'):
                phonetic_vowels.append('uu' if language == 'hi' else 'oo')
            elif m == 'ai':
                phonetic_vowels.append('ai')
            elif m in ('au', 'ou'):
                phonetic_vowels.append('au')
            elif m == 'a':
                if is_final and len(matches) > 1:
                    phonetic_vowels.append('aa')
                else:
                    phonetic_vowels.append('a')
            elif m == 'i':
                if is_final and len(matches) > 1:
                    phonetic_vowels.append('ii' if language == 'hi' else 'ee')
                else:
                    phonetic_vowels.append('i')
            elif m == 'u':
                phonetic_vowels.append('u')
            elif m == 'e':
                phonetic_vowels.append('e' if language == 'hi' else 'ee')
            elif m == 'o':
                phonetic_vowels.append('o' if language == 'hi' else 'oo')
            elif m == 'y':
                phonetic_vowels.append('i')
            else:
                phonetic_vowels.append('a')
                
        vowel_seq = "-".join(phonetic_vowels)
        exact_key = word_clean[-2:] if len(word_clean) >= 2 else word_clean
        return vowel_seq, exact_key, len(phonetic_vowels)

    async def load_romanized_words_map(self, session: AsyncSession):
        """Load registered Romanized words from database into in-memory map for fast highlight lookups"""
        try:
            query = select(MultisyllabicWord).where(MultisyllabicWord.language.in_(['hi', 'kn']))
            res = await session.execute(query)
            words = res.scalars().all()
            
            count = 0
            for w in words:
                w_lower = w.word.strip().lower()
                if w_lower.isalpha() and all(ord(c) < 128 for c in w_lower):
                    self.romanized_words_map[w_lower] = w.language
                    count += 1
            print(f"[INFO] Loaded {count} Romanized Hindi/Kannada words into memory map.")
        except Exception as e:
            print(f"[WARNING] Failed to load romanized words map: {e}")

    async def auto_register_word(
        self, session: AsyncSession, word: str, language: str, 
        vowel_seq: str, exact_key: str, syllable_count: int
    ):
        """Dynamically add new search terms to the local dictionary to self-learn vocabulary"""
        word_clean = word.strip()
        if not word_clean:
            return
            
        query = select(MultisyllabicWord).where(
            MultisyllabicWord.language == language,
            func.lower(MultisyllabicWord.word) == word_clean.lower()
        )
        res = await session.execute(query)
        exists = res.scalar()
        
        if not exists:
            new_word = MultisyllabicWord(
                word=word_clean,
                language=language,
                syllable_count=syllable_count,
                vowel_sequence=vowel_seq,
                exact_rhyme_key=exact_key,
                is_slang=False,
                upvotes=1
            )
            session.add(new_word)
            try:
                await session.commit()
                # Update in-memory map
                w_lower = word_clean.lower()
                if w_lower.isalpha() and all(ord(c) < 128 for c in w_lower):
                    self.romanized_words_map[w_lower] = language
            except Exception:
                await session.rollback()

    async def find_combinatorial_rhymes(
        self, session: AsyncSession, vowel_seq: str, language: str, 
        allow_slang: bool = True, max_results: int = 20
    ) -> List[dict]:
        """Combinatorial Multi-Word Search: combines shorter words matching parts of the vowel sequence"""
        vparts = vowel_seq.split("-")
        n = len(vparts)
        if n < 2:
            return []
            
        results = []
        seen = set()
        
        # Split target vowel sequence into two back-to-back word templates
        for k in range(1, n):
            part_a = "-".join(vparts[:k])
            part_b = "-".join(vparts[k:])
            
            # Match part A
            query_a = select(MultisyllabicWord).where(
                MultisyllabicWord.language == language,
                MultisyllabicWord.vowel_sequence == part_a
            )
            if not allow_slang:
                query_a = query_a.where(MultisyllabicWord.is_slang == False)
            query_a = query_a.order_by(MultisyllabicWord.upvotes.desc()).limit(15)
            res_a = await session.execute(query_a)
            words_a = res_a.scalars().all()
            
            # Match part B
            query_b = select(MultisyllabicWord).where(
                MultisyllabicWord.language == language,
                MultisyllabicWord.vowel_sequence == part_b
            )
            if not allow_slang:
                query_b = query_b.where(MultisyllabicWord.is_slang == False)
            query_b = query_b.order_by(MultisyllabicWord.upvotes.desc()).limit(15)
            res_b = await session.execute(query_b)
            words_b = res_b.scalars().all()
            
            for wa in words_a:
                for wb in words_b:
                    combo = f"{wa.word} {wb.word}"
                    if combo.lower() not in seen:
                        seen.add(combo.lower())
                        results.append({
                            "word": combo,
                            "syllable_count": wa.syllable_count + wb.syllable_count,
                            "vowel_sequence": f"{wa.vowel_sequence}-{wb.vowel_sequence}",
                            "upvotes": wa.upvotes + wb.upvotes,
                            "is_slang": wa.is_slang or wb.is_slang
                        })
                        
        results.sort(key=lambda x: x["upvotes"], reverse=True)
        return results[:max_results]

    def get_detailed_stress_layout(self, word: str, language: str) -> str:
        """Get stress pattern (x = unstressed/Lagu, / = stressed/Guru) for a word based on language"""
        word = word.strip().lower()
        if not word:
            return ""
            
        if language == 'en':
            # Use CMUDict stresses
            word_clean = re.sub(r'[^a-z]', '', word)
            if not word_clean:
                return "x"
            phones_list = pronouncing.phones_for_word(word_clean)
            if phones_list:
                stress = pronouncing.stresses(phones_list[0])
                return stress.replace('1', '/').replace('2', '/').replace('0', 'x')
            else:
                # Fallback: guess unstressed for vowel groups
                vowels = re.findall(r'[aeiouy]+', word_clean)
                return "x" * max(1, len(vowels))
                
        elif language in ('hi', 'kn'):
            # Hindi/Kannada Swara and Matra extraction is vowel-based
            vowel_seq, _, _ = self.extract_vowels(word, language)
            if not vowel_seq:
                return "x"
            parts = vowel_seq.split("-")
            
            # Map Hindi / Kannada vowels to Lagu/Guru
            if language == 'hi':
                long_vowels = {'aa', 'ii', 'uu', 'e', 'ai', 'o', 'au', 'ri'}
            else: # kn
                long_vowels = {'aa', 'ii', 'uu', 'ee', 'oo', 'ai', 'au'}
                
            layout = []
            for p in parts:
                if p.lower() in long_vowels:
                    layout.append('/')
                else:
                    layout.append('x')
            return "".join(layout)
            
        else:
            vowels = re.findall(r'[aeiouy]+', word)
            return "x" * max(1, len(vowels))

    async def find_doppelreim_rhymes(
        self, session: AsyncSession, word: str, language: str = 'en', 
        mode: str = 'vowel', allow_slang: bool = True, max_results: int = 30,
        target_syllables: Optional[int] = None, target_stress: Optional[str] = None
    ) -> List[dict]:
        """Main entrypoint for advanced multisyllabic lookup with rhythmic ranking options"""
        word = word.strip()
        if not word:
            return []
            
        cache_key = (word.lower(), language, mode, allow_slang, max_results, target_syllables, target_stress)
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]
            
        vowel_seq, exact_key, syllable_count = self.extract_vowels(word, language)
        
        # Self-learning step: add query word if it's missing
        await self.auto_register_word(session, word, language, vowel_seq, exact_key, syllable_count)
        
        def calculate_rhythmic_score(cand_syllables: int, cand_stress: str) -> float:
            score = 0.0
            if target_syllables is not None:
                diff = abs(cand_syllables - target_syllables)
                score -= diff * 2.0  # heavy penalty for syllable count difference
            if target_stress:
                match_chars = 0
                clean_target = target_stress.replace(" ", "")
                clean_cand = cand_stress.replace(" ", "")
                min_len = min(len(clean_cand), len(clean_target))
                for idx in range(min_len):
                    if clean_cand[idx] == clean_target[idx]:
                        match_chars += 1
                if min_len > 0:
                    score += (match_chars / max(len(clean_cand), len(clean_target))) * 3.0
            return score

        if mode == 'multi':
            res = await self.find_combinatorial_rhymes(session, vowel_seq, language, allow_slang, max_results)
            # Add stress pattern to combinatorial results
            for r in res:
                r["stress_pattern"] = self.get_detailed_stress_layout(r["word"], language)
                if target_syllables is not None or target_stress:
                    r["rhythmic_score"] = calculate_rhythmic_score(r["syllable_count"], r["stress_pattern"])
            
            if target_syllables is not None or target_stress:
                res.sort(key=lambda x: (x.get("rhythmic_score", 0.0), x["upvotes"]), reverse=True)
                
            final_res = res[:max_results]
            self._cache[cache_key] = final_res
            if len(self._cache) > self._cache_max_size:
                self._cache.popitem(last=False)
            return final_res
            
        query = select(MultisyllabicWord).where(MultisyllabicWord.language == language)
        
        if mode == 'classic':
            query = query.where(MultisyllabicWord.exact_rhyme_key == exact_key)
        else:  # vowel / slant / inspiration
            query = query.where(MultisyllabicWord.vowel_sequence == vowel_seq)
            
        if not allow_slang:
            query = query.where(MultisyllabicWord.is_slang == False)
            
        query = query.order_by(MultisyllabicWord.upvotes.desc()).limit(max_results)
        res = await session.execute(query)
        words = res.scalars().all()
        
        results = []
        for w in words:
            if w.word.lower() != word.lower():
                cand_stress = self.get_detailed_stress_layout(w.word, language)
                results.append({
                    "word": w.word,
                    "syllable_count": w.syllable_count,
                    "vowel_sequence": w.vowel_sequence,
                    "exact_key": w.exact_rhyme_key,
                    "upvotes": w.upvotes,
                    "is_slang": w.is_slang,
                    "stress_pattern": cand_stress
                })
                
        # Classic fallback to Vowel/Slant when perfect matches are sparse
        if mode == 'classic' and len(results) < 5:
            vowel_results = await self.find_doppelreim_rhymes(
                session, word, language, 'vowel', allow_slang, max_results, target_syllables, target_stress
            )
            existing = {r["word"].lower() for r in results}
            for r in vowel_results:
                if r["word"].lower() not in existing:
                    results.append(r)
                    
        # Apply rhythmic score and re-sort if targets are specified
        if target_syllables is not None or target_stress:
            for r in results:
                if "stress_pattern" not in r:
                    r["stress_pattern"] = self.get_detailed_stress_layout(r["word"], language)
                r["rhythmic_score"] = calculate_rhythmic_score(r["syllable_count"], r["stress_pattern"])
            results.sort(key=lambda x: (x.get("rhythmic_score", 0.0), x["upvotes"]), reverse=True)
            
        final_results = results[:max_results]
        self._cache[cache_key] = final_results
        if len(self._cache) > self._cache_max_size:
            self._cache.popitem(last=False)
            
        return final_results

    async def seed_phonetic_database(self, session: AsyncSession):
        """Seed the multisyllabic dictionary with standard words for English, Hindi, and Kannada"""
        # Always populate the in-memory romanized words map first
        await self.load_romanized_words_map(session)
        
        query = select(func.count()).select_from(MultisyllabicWord)
        res = await session.execute(query)
        count = res.scalar() or 0
        if count > 0:
            print("[INFO] Phonetic database already seeded.")
            return
            
        print("[*] Seeding phonetic database (offline CMUDict & Indian languages)...")
        
        words_to_insert = []
        
        # 1. English Seeding via CMUDict
        try:
            pronouncing.init_cmu()
            if pronouncing.pronunciations:
                print(f"[*] Found {len(pronouncing.pronunciations)} English pronunciations. Processing...")
                seen_words = set()
                for word, phones in pronouncing.pronunciations:
                    clean = word.strip().lower()
                    if not clean or clean in seen_words or not clean.isalpha():
                        continue
                    seen_words.add(clean)
                    
                    vowel_parts = []
                    for p in phones.split():
                        if p[-1].isdigit():
                            vowel_parts.append(p)
                    vowel_seq = "-".join(vowel_parts)
                    exact_key = pronouncing.rhyming_part(phones) or ""
                    syllable_count = pronouncing.syllable_count(phones)
                    
                    words_to_insert.append({
                        "word": word,
                        "language": "en",
                        "syllable_count": syllable_count,
                        "vowel_sequence": vowel_seq,
                        "exact_rhyme_key": exact_key,
                        "is_slang": False,
                        "upvotes": 5
                    })
        except Exception as e:
            print(f"[!] English seeding failed: {e}")
            
        # 2. Hindi Vocabulary Seed
        hindi_vocab = [
            "अपना", "सपना", "प्यार", "यार", "दिल", "महान", "खटका", "सबका", "कहना", "रहना", 
            "जिंदगी", "मौत", "दोस्त", "दुश्मन", "रास्ता", "मंजिल", "आसमान", "धरती", "दुनिया", "इंसान", 
            "खुदा", "रब", "दुआ", "सलाम", "काम", "नाम", "दाम", "शाम", "सुबह", "रात", 
            "दिन", "बात", "हात", "साथ", "माथ", "आज", "कल", "पल", "चल", "बल", 
            "घर", "पर", "दर", "सर", "हर", "कर", "भर", "मर", "डर", "शायर", "कविता", "गाने",
            "प्यारी", "सच्चा", "झूठा", "धोखा", "कामयाबी", "मेहनत", "कोशिश", "मंज़िल", "सफ़र", "राही",
            "नसीब", "तकदीर", "हौसला", "हिम्मत", "जुनून", "सच्चाई", "अपनो", "सपनो", "यारी", "दोस्ती"
        ]
        for hw in hindi_vocab:
            vseq, ekey, syl = self.extract_hindi_vowels(hw)
            words_to_insert.append({
                "word": hw,
                "language": "hi",
                "syllable_count": syl,
                "vowel_sequence": vseq,
                "exact_rhyme_key": ekey,
                "is_slang": False,
                "upvotes": 5
            })
            
        # 3. Kannada Vocabulary Seed
        kannada_vocab = [
            "ಬಂಗಾರ", "ಮಸ್ತಕ", "ಪುಸ್ತಕ", "ಕನ್ನಡ", "ಹಾಡು", "ಮಾಡು", "ನೋಡು", "ಹೇಳು", "ಕೇಳು", "ಬರೆಯು", 
            "ಓದು", "ದುಡ್ಡು", "ಕೊಡು", "ತಗೋ", "ಹೋಗು", "ಬಾ", "ನಮಸ್ಕಾರ", "ಪ್ರೀತಿ", "ಸ್ನೇಹ", "ಜೀವನ", 
            "ಖುಷಿ", "ದುಃಖ", "ಕನಸು", "ಮನಸು", "ನೆನಪು", "ಕಾಲ", "ಲೋಕ", "ಜನ", "ಮನೆ", "ಕಾಡು", 
            "ನಾಡು", "ಊರು", "ಕೆರೆ", "ಹೊಳೆ", "ನದಿ", "ಸಮುದ್ರ", "ಬೆಟ್ಟ", "ಗುಡ್ಡ", "ಕಲ್ಲು", "ಮಣ್ಣು", 
            "ನೀರು", "ಗಾಳಿ", "ಬೆಂಕಿ", "ಆಕಾಶ", "ಭೂಮಿ", "ಸೂರ್ಯ", "ಚಂದ್ರ", "ನಕ್ಷತ್ರ", "ಹಗಲು", "ರಾತ್ರಿ",
            "ಪ್ರೀತಿಯ", "ಸತ್ಯ", "ಸುಳ್ಳು", "ಮೋಸ", "ಗೆಲುವು", "ಶ್ರಮ", "ಪ್ರಯತ್ನ", "ದಾರಿ", "ಪಯಣ", "ಗುರಿ",
            "ಹಣೆಬರಹ", "ಧೈರ್ಯ", "ಉತ್ಸಾಹ", "ನನ್ನವರು", "ನಿನ್ನವರು", "ನಮ್ಮವರು", "ಸ್ನೇಹಿತ", "ಬಾಳು", "ಸಾವು"
        ]
        for kw in kannada_vocab:
            vseq, ekey, syl = self.extract_kannada_vowels(kw)
            words_to_insert.append({
                "word": kw,
                "language": "kn",
                "syllable_count": syl,
                "vowel_sequence": vseq,
                "exact_rhyme_key": ekey,
                "is_slang": False,
                "upvotes": 5
            })
        
        # 4. Romanized Hindi (Hinglish) Vocabulary Seed
        hinglish_vocab = [
            "apna", "sapna", "pyaar", "yaar", "dil", "mahaan", "khatka", "sabka", "kehna", "rehna",
            "zindagi", "maut", "dost", "dushman", "raasta", "manzil", "aasmaan", "dharti", "duniya", "insaan",
            "khuda", "rab", "dua", "salaam", "kaam", "naam", "daam", "shaam", "subah", "raat",
            "din", "baat", "haath", "saath", "maath", "aaj", "kal", "pal", "chal", "bal",
            "ghar", "par", "dar", "sar", "har", "kar", "bhar", "mar", "sharr", "shaayar", "kavita", "gaane",
            "ishq", "mohabbat", "dard", "khushi", "gham", "aansu", "rona", "hasna", "jeena", "marna",
            "taqdeer", "kismat", "naseeb", "imtihaan", "safar", "musafir", "raahi", "manzilen",
            "sitaare", "chaand", "suraj", "badal", "baarish", "paani", "aag", "hawa", "zameen",
            "pathar", "phool", "kaanta", "dariya", "saagar", "toofaan", "bijli", "dhoop", "chaaya",
            "sapne", "neend", "jaagna", "sochna", "bolna", "sunna", "dekhna", "milna", "jaana",
            "aana", "lautna", "bhoolna", "yaad", "waqt", "lamha", "arzoo", "tamanna", "umeed",
            "hausla", "himmat", "junoon", "firaaq", "judai", "milan", "vaada", "dhoka",
            "bewafa", "aashiq", "deewana", "majnoon", "laila", "mehfil", "jalsa", "tamaasha",
            "dhamaka", "shor", "khamoshi", "sukoon", "aman", "jung", "talwaar",
            # Expanded Hinglish vocabulary (50 new words)
            "apne", "sapno", "yaara", "pyaara", "dosti", "asli", "nakli", "dhokebaaz",
            "shana", "dedh-shana", "bhai", "bhaijaan", "pateli", "rap", "hiphop", "flow",
            "machaenge", "dhamaal", "vibe", "scene", "hard", "boht-hard", "public", "bawa",
            "khauf", "darr", "gully", "sadak", "paisa", "kamana", "udaana", "kharcha",
            "fame", "naam-o-nishan", "koshish", "kamyabi", "haunsla", "jazba", "mehnat",
            "junooni", "manzil-e-maqsood", "safar-nama", "raah", "manzilein", "kadam", "manaa",
            "darza", "hukumat", "raaj", "badshah", "wazir", "shatranj", "chaal", "maat"
        ]
        for hw in hinglish_vocab:
            vseq, ekey, syl = self.extract_romanized_indian_vowels(hw, 'hi')
            words_to_insert.append({
                "word": hw,
                "language": "hi",
                "syllable_count": syl,
                "vowel_sequence": vseq,
                "exact_rhyme_key": ekey,
                "is_slang": False,
                "upvotes": 5
            })
            
        # 5. Romanized Kannada (Kanglish) Vocabulary Seed
        kanglish_vocab = [
            "bangaara", "mastaka", "pustaka", "kannada", "haadu", "maadu", "noodu", "helu", "kelu", "bareyu",
            "oodu", "duddu", "kodu", "tago", "hogu", "baa", "namaskaara", "preethi", "sneha", "jeevana",
            "khushi", "dukkha", "kanasu", "manasu", "nenapu", "kaala", "loka", "jana", "mane", "kaadu",
            "naadu", "ooru", "kere", "hole", "nadi", "samudra", "betta", "gudda", "kallu", "mannu",
            "neeru", "gaali", "benki", "aakaasha", "bhoomi", "soorya", "chandra", "nakshatra", "hagalu", "raathri",
            "hudugi", "huduga", "amme", "appa", "anna", "akka", "thambi", "thangala",
            "yenu", "illi", "alli", "hegidiya", "baalige", "hogona", "barona", "ninage", "nanage",
            "preethse", "onde", "maathadu", "nodidya", "kelide", "gottu", "gottilla",
            "chennagide", "tumba", "kashta", "santhosa", "devaru", "manushya", "hrudaya",
            "baaluva", "haakuva", "iruva", "aguva", "baruva", "hogova", "maadona",
            # Expanded Kanglish vocabulary (50 new words)
            "macha", "bro", "guru", "sisya", "magane", "hudugru", "hudugiru", "bejaan",
            "tumba-chennagide", "sakath", "kirik", "dhool", "dhamaka", "kannadiga", "karnataka",
            "namdu", "nimdu", "namma", "nimma", "naavu", "neevu", "yella", "sari", "helpa",
            "kelsa", "dundu", "kasu", "paisa", "raja", "mantri", "aata", "oota", "neeru",
            "sneha-bandha", "prema-kavya", "hrudaya-bhaava", "manase", "kanase", "baduku",
            "savu", "jana-gana", "loka-bandhu", "oora-devru", "kaada-bettu", "hadu-hadu",
            "bari-bari", "nod-nod", "kel-kel", "hog-hog", "baa-baa"
        ]
        for kw in kanglish_vocab:
            vseq, ekey, syl = self.extract_romanized_indian_vowels(kw, 'kn')
            words_to_insert.append({
                "word": kw,
                "language": "kn",
                "syllable_count": syl,
                "vowel_sequence": vseq,
                "exact_rhyme_key": ekey,
                "is_slang": False,
                "upvotes": 5
            })

        # 6. English Slang Seeding (37 hip-hop terms)
        english_slang = [
            ("flex", "EH", "EH-K-S", 1),
            ("drip", "IH", "IH-P", 1),
            ("cap", "AE", "AE-P", 1),
            ("opps", "AA", "AA-P-S", 1),
            ("finna", "IH-AH", "AH", 2),
            ("whip", "IH", "IH-P", 1),
            ("guap", "AA", "AA-P", 1),
            ("clout", "AW", "AW-T", 1),
            ("fam", "AE", "AE-M", 1),
            ("squad", "AA", "AA-D", 1),
            ("stan", "AE", "AE-N", 1),
            ("sauce", "AO", "AO-S", 1),
            ("vibe", "AY", "AY-B", 1),
            ("hustle", "AH-AH", "AH-L", 2),
            ("grind", "AY", "AY-N-D", 1),
            ("flows", "OW", "OW-Z", 1),
            ("rhymes", "AY", "AY-M-Z", 1),
            ("beats", "IY", "IY-T-S", 1),
            ("spit", "IH", "IH-T", 1),
            ("bars", "AA", "AA-R-Z", 1),
            ("homie", "OW-IY", "IY", 2),
            ("dope", "OW", "OW-P", 1),
            ("lit", "IH", "IH-T", 1),
            ("fire", "AY-ER", "AY-ER", 2),
            ("crunk", "AH", "AH-NG-K", 1),
            ("banger", "AE-ER", "ER", 2),
            ("steez", "IY", "IY-Z", 1),
            ("ghost", "OW", "OW-S-T", 1),
            ("shook", "UH-K", "UH-K", 1),
            ("bounce", "AW", "AW-N-S", 1),
            ("hustler", "AH-ER", "ER", 2),
            ("trippin", "IH-IH", "IH-N", 2),
            ("ballin", "AO-IH", "IH-N", 2),
            ("savage", "AE-IH", "IH-JH", 2),
            ("salty", "AO-IY", "IY", 2),
            ("boujee", "UW-IY", "IY", 2),
            ("homies", "OW-IY-Z", "IY-Z", 2)
        ]
        for word, vseq, ekey, syl in english_slang:
            words_to_insert.append({
                "word": word,
                "language": "en",
                "syllable_count": syl,
                "vowel_sequence": vseq,
                "exact_rhyme_key": ekey,
                "is_slang": True,
                "upvotes": 10
            })

        # Chunk bulk insertion to keep SQLite transactions light
        chunk_size = 5000
        total = len(words_to_insert)
        print(f"[*] Total {total} words processed for database insertion. Executing bulk insert...")
        
        for idx in range(0, total, chunk_size):
            chunk = words_to_insert[idx : idx + chunk_size]
            await session.execute(
                insert(MultisyllabicWord),
                chunk
            )
            print(f"  -> Inserted {min(idx + chunk_size, total)} / {total}")
            
        await session.commit()
        print("[OK] Seeding phonetic database completed successfully.")
    
    @lru_cache(maxsize=1000)
    def find_rhymes(self, word: str, max_results: int = 20) -> List[str]:
        """Find rhyming words"""
        word = word.lower().strip()
        if not word:
            return []
        
        rhymes = set()
        
        # CMU dictionary rhymes
        try:
            cmu_rhymes = pronouncing.rhymes(word)
            rhymes.update(cmu_rhymes[:max_results])
        except Exception:
            pass
        
        # Hip-hop family rhymes
        ending = self._get_ending(word)
        for family in self.RHYME_FAMILIES + self.INDIAN_FAMILIES:
            if ending in family:
                for other_ending in family:
                    if other_ending != ending:
                        # Generate potential rhymes
                        base = word[:-len(ending)] if word.endswith(ending) else word
                        rhymes.add(base + other_ending)
        
        return list(rhymes)[:max_results]
    
    def _get_ending(self, word: str) -> str:
        """Get the rhyme-relevant ending of a word"""
        vowels = 'aeiouy'
        word = word.lower()
        
        # Find last vowel position
        last_vowel_pos = -1
        for i, char in enumerate(word):
            if char in vowels:
                last_vowel_pos = i
        
        if last_vowel_pos >= 0:
            return word[last_vowel_pos:]
        return word[-2:] if len(word) >= 2 else word
    
    def get_rhyme_ending(self, word: str) -> str:
        """Get the phonetic rhyme ending"""
        word = word.lower().strip()
        if any(0x0900 <= ord(c) <= 0x097F for c in word):
            # Hindi
            word = re.sub(r'[^\u0900-\u097f]', '', word)
            return word[-2:] if len(word) >= 2 else word
        elif any(0x0C80 <= ord(c) <= 0x0CFF for c in word):
            # Kannada
            word = re.sub(r'[^\u0c80-\u0cff]', '', word)
            return word[-2:] if len(word) >= 2 else word
        else:
            word = re.sub(r'[^a-z]', '', word)
            phones = pronouncing.phones_for_word(word)
            if phones:
                # Get rhyme part (from last stressed vowel)
                return pronouncing.rhyming_part(phones[0])
            return self._get_ending(word)
    
    def find_multi_syllable_rhymes(self, word: str) -> List[str]:
        """Find multi-syllable rhymes"""
        word = word.lower().strip()
        rhymes = []
        
        phones = pronouncing.phones_for_word(word)
        if phones:
            syllable_count = pronouncing.syllable_count(phones[0])
            
            # Find words with similar syllable count that rhyme
            base_rhymes = self.find_rhymes(word, max_results=50)
            for rhyme in base_rhymes:
                r_phones = pronouncing.phones_for_word(rhyme)
                if r_phones and pronouncing.syllable_count(r_phones[0]) >= syllable_count:
                    rhymes.append(rhyme)
        
        return rhymes[:20]
    
    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms (simplified version)"""
        # Would integrate with NLTK WordNet in full version
        return []
    
    def highlight_lyrics(self, lines: List[str]) -> List[str]:
        """
        Professional-grade multi-layer rhyme highlighting.

        Detection layers (each gets a distinct visual treatment):
        1. Perfect end-rhymes  → solid color background
        2. Near/slant rhymes   → dashed-border variant
        3. Assonance           → colored bottom-border (vowel match)
        4. Consonance          → dotted underline (consonant match)
        5. Internal rhymes     → within-line rhyme pairs
        6. Multi-syllable      → glow effect for 2+ syllable rhymes
        7. Alliteration        → italic underline

        Sub-word highlighting: only the rhyming portion of each word is colored.
        """
        if not lines:
            return []

        # ── 1. Tokenize ──────────────────────────────────────────────
        all_words: List[str] = []          # clean words
        all_phones: List[str] = []         # CMU phoneme strings ('' if unknown)
        all_rhyme_parts: List[str] = []    # rhyming part (from last stressed vowel)
        word_line: List[int] = []          # line index per word
        word_original: List[str] = []      # original (un-cleaned) word
        word_map: List[List[int]] = []     # per-line list of flat indices

        for i, line in enumerate(lines):
            words = line.split()
            wm: List[int] = []
            for word in words:
                # Detect language
                is_hindi = any(0x0900 <= ord(c) <= 0x097F for c in word)
                is_kannada = any(0x0C80 <= ord(c) <= 0x0CFF for c in word)
                
                if is_hindi:
                    clean = re.sub(r'[^\u0900-\u097f]', '', word)
                    lang = 'hi'
                elif is_kannada:
                    clean = re.sub(r'[^\u0c80-\u0cff]', '', word)
                    lang = 'kn'
                else:
                    clean = re.sub(r'[^a-z]', '', word.lower())
                    lang = self.romanized_words_map.get(clean, 'en')
                    
                if clean:
                    if lang == 'en':
                        phones_list = pronouncing.phones_for_word(clean)
                        phones = phones_list[0] if phones_list else ''
                        rp = pronouncing.rhyming_part(phones) if phones else self._get_ending(clean)
                    else:
                        vowel_seq, exact_key, _ = self.extract_vowels(clean, lang)
                        # Space-separated vowels for pronunciation mapping compatibility
                        phones = vowel_seq.replace('-', ' ')
                        rp = exact_key

                    all_words.append(clean)
                    all_phones.append(phones)
                    all_rhyme_parts.append(rp)
                    word_line.append(i)
                    word_original.append(word)
                    wm.append(len(all_words) - 1)
                else:
                    wm.append(-1)
            word_map.append(wm)

        n = len(all_words)
        if n == 0:
            return list(lines)

        # Per-word decoration accumulator: idx -> set of css classes
        word_classes: Dict[int, set] = {i: set() for i in range(n)}
        # Per-word data attributes (for tooltips etc.)
        word_data: Dict[int, Dict[str, str]] = {i: {} for i in range(n)}

        # ── 2. Perfect end-rhyme groups ──────────────────────────────
        sound_groups: Dict[str, List[int]] = {}
        for idx, rp in enumerate(all_rhyme_parts):
            if rp:
                sound_groups.setdefault(rp, []).append(idx)

        # Filter: 2+ words across 2+ lines
        perfect_groups: Dict[str, List[int]] = {}
        for rp, indices in sound_groups.items():
            if len(indices) >= 2:
                lines_involved = set(word_line[idx] for idx in indices)
                if len(lines_involved) >= 2:
                    perfect_groups[rp] = indices

        # Assign colors — most frequent first
        group_colors: Dict[str, str] = {}
        color_idx = 0
        for rp, indices in sorted(perfect_groups.items(), key=lambda x: len(x[1]), reverse=True):
            group_colors[rp] = f"rhyme-group-{color_idx % 12 + 1}"
            color_idx += 1

        for rp, indices in perfect_groups.items():
            css = group_colors[rp]
            for idx in indices:
                word_classes[idx].add(css)
                word_classes[idx].add("rhyme-word")

        # ── 3. Multi-syllable rhyme detection ────────────────────────
        # Check if any perfect-rhyme pair shares 4+ trailing phonemes
        for rp, indices in perfect_groups.items():
            if len(indices) < 2:
                continue
            # Check first pair to determine multi-syllable
            ref_phones = all_phones[indices[0]]
            if not ref_phones:
                continue
            for idx in indices[1:]:
                if all_phones[idx] and self._is_multi_syllable_rhyme(ref_phones, all_phones[idx]):
                    for i2 in indices:
                        word_classes[i2].add("multi-syl-rhyme")
                    break

        # ── 4. Near / Slant rhymes ───────────────────────────────────
        # Find pairs where rhyming parts differ by exactly 1 phoneme
        rp_keys = list(sound_groups.keys())
        near_groups_merged: Dict[int, str] = {}  # word idx -> near-rhyme css class
        near_color_idx = 0
        already_near_paired = set()

        for i_rp, rp1 in enumerate(rp_keys):
            for j_rp in range(i_rp + 1, len(rp_keys)):
                rp2 = rp_keys[j_rp]
                pair_key = (rp1, rp2) if rp1 < rp2 else (rp2, rp1)
                if pair_key in already_near_paired:
                    continue
                # Skip if either is already a perfect rhyme group
                if rp1 in perfect_groups and rp2 in perfect_groups:
                    continue
                dist = self._phoneme_distance(rp1, rp2)
                if dist <= 1.0:
                    already_near_paired.add(pair_key)
                    combined = sound_groups[rp1] + sound_groups[rp2]
                    # Require cross-line
                    lines_involved = set(word_line[idx] for idx in combined)
                    if len(lines_involved) >= 2 and len(combined) >= 2:
                        css = f"near-group-{near_color_idx % 6 + 1}"
                        near_color_idx += 1
                        for idx in combined:
                            if "rhyme-word" not in word_classes[idx]:
                                word_classes[idx].add("near-rhyme")
                                word_classes[idx].add(css)

        # ── 5. Assonance (shared stressed vowel, different ending) ───
        vowel_groups: Dict[str, List[int]] = {}
        for idx in range(n):
            vowel = self._get_stressed_vowel(all_phones[idx])
            if vowel:
                vowel_groups.setdefault(vowel, []).append(idx)

        asso_color_idx = 0
        for vowel, indices in sorted(vowel_groups.items(), key=lambda x: len(x[1]), reverse=True):
            # Only words NOT already highlighted as perfect rhymes
            candidates = [i for i in indices if "rhyme-word" not in word_classes[i]]
            lines_involved = set(word_line[i] for i in candidates)
            if len(candidates) >= 3 and len(lines_involved) >= 2:
                css = f"assonance-{asso_color_idx % 6 + 1}"
                asso_color_idx += 1
                for idx in candidates:
                    word_classes[idx].add("assonance")
                    word_classes[idx].add(css)
                    word_data[idx]["data-vowel"] = vowel

        # ── 6. Consonance (shared consonant skeleton) ────────────────
        cons_groups: Dict[str, List[int]] = {}
        for idx in range(n):
            clean_word = all_words[idx]
            is_hindi = any(0x0900 <= ord(c) <= 0x097F for c in clean_word)
            is_kannada = any(0x0C80 <= ord(c) <= 0x0CFF for c in clean_word)
            
            if is_hindi:
                consonants = [c for c in clean_word if (0x0915 <= ord(c) <= 0x0939) or (0x0958 <= ord(c) <= 0x095F) or c == 'ळ']
                frame = "_".join(consonants) if len(consonants) >= 2 else ""
            elif is_kannada:
                consonants = [c for c in clean_word if (0x0C95 <= ord(c) <= 0x0CB9) or ord(c) == 0x0CDE]
                frame = "_".join(consonants) if len(consonants) >= 2 else ""
            else:
                frame = self._get_consonant_frame(all_phones[idx])
                
            if frame and len(frame) >= 2:  # at least 2 consonants
                cons_groups.setdefault(frame, []).append(idx)

        for frame, indices in cons_groups.items():
            candidates = [i for i in indices if "rhyme-word" not in word_classes[i] and "assonance" not in word_classes[i]]
            lines_involved = set(word_line[i] for i in candidates)
            if len(candidates) >= 2 and len(lines_involved) >= 2:
                for idx in candidates:
                    word_classes[idx].add("consonance")

        # ── 7. Internal rhymes (within-line pairs) ───────────────────
        for i, line in enumerate(lines):
            line_indices = [fi for fi in word_map[i] if fi != -1]
            if len(line_indices) < 2:
                continue
            for a_pos in range(len(line_indices)):
                for b_pos in range(a_pos + 1, len(line_indices)):
                    a_idx = line_indices[a_pos]
                    b_idx = line_indices[b_pos]
                    rp_a = all_rhyme_parts[a_idx]
                    rp_b = all_rhyme_parts[b_idx]
                    if rp_a and rp_b and rp_a == rp_b and all_words[a_idx] != all_words[b_idx]:
                        word_classes[a_idx].add("internal-rhyme")
                        word_classes[b_idx].add("internal-rhyme")

        # ── 8. Alliteration ──────────────────────────────────────────
        for i, line in enumerate(lines):
            words = line.split()
            cleans = [re.sub(r'[^a-z]', '', w.lower()) for w in words]
            first_chars: Dict[str, List[int]] = {}
            for j, c in enumerate(cleans):
                if c:
                    first_chars.setdefault(c[0], []).append(j)
            for char, js in first_chars.items():
                if len(js) >= 2:
                    for j in js:
                        fi = word_map[i][j]
                        if fi != -1:
                            word_classes[fi].add("alliteration")

        # ── 9. Build HTML with sub-word phoneme highlighting ─────────
        highlighted_lines = []
        for i, line in enumerate(lines):
            words = line.split()
            if not words:
                highlighted_lines.append(line)
                continue

            parts = []
            for j, word in enumerate(words):
                fi = word_map[i][j]
                if fi == -1 or not word_classes[fi]:
                    parts.append(word)
                    continue

                classes = word_classes[fi]
                cls_str = ' '.join(sorted(classes))

                # Data attributes
                data_str = ''
                for dk, dv in word_data.get(fi, {}).items():
                    data_str += f" {dk}='{dv}'"

                # Sub-word highlighting: split at rhyme boundary
                if "rhyme-word" in classes or "near-rhyme" in classes:
                    prefix, rhyme_suffix = self._split_word_at_rhyme(
                        word, all_words[fi], all_phones[fi]
                    )
                    if prefix and rhyme_suffix:
                        parts.append(f"{prefix}<span class='{cls_str}'{data_str}>{rhyme_suffix}</span>")
                    else:
                        parts.append(f"<span class='{cls_str}'{data_str}>{word}</span>")
                else:
                    parts.append(f"<span class='{cls_str}'{data_str}>{word}</span>")

            highlighted_lines.append(" ".join(parts))

        return highlighted_lines

    # ── Detection helper methods ─────────────────────────────────────

    def detect_internal_rhymes(self, line: str) -> bool:
        """Check if a line contains internal rhymes (rhymes within the same line)."""
        words = line.split()
        if len(words) < 2:
            return False

        rhyme_parts = []
        for word in words:
            clean = re.sub(r'[^a-z]', '', word.lower())
            if not clean:
                rhyme_parts.append('')
                continue
            phones_list = pronouncing.phones_for_word(clean)
            if phones_list:
                rhyme_parts.append(pronouncing.rhyming_part(phones_list[0]))
            else:
                rhyme_parts.append(self._get_ending(clean))

        # Check for any pair with matching rhyme part (different words)
        cleans = [re.sub(r'[^a-z]', '', w.lower()) for w in words]
        for i_w in range(len(rhyme_parts)):
            for j_w in range(i_w + 1, len(rhyme_parts)):
                if (rhyme_parts[i_w] and rhyme_parts[j_w]
                        and rhyme_parts[i_w] == rhyme_parts[j_w]
                        and cleans[i_w] != cleans[j_w]):
                    return True
        return False

    def _split_word_at_rhyme(self, original: str, clean: str, phones: str) -> tuple:
        """
        Split a word into (prefix, rhyme_suffix) for sub-word highlighting.
        Uses phoneme-to-grapheme alignment to find where the rhyme starts.

        E.g., 'scars' with rhyming part 'AA1 R Z' → ('sc', 'ars')
              'boat'  with rhyming part 'OW1 T'   → ('b', 'oat')
        """
        is_hindi = any(0x0900 <= ord(c) <= 0x097F for c in clean)
        is_kannada = any(0x0C80 <= ord(c) <= 0x0CFF for c in clean)
        
        if is_hindi or is_kannada:
            if len(original) >= 3:
                return (original[:-2], original[-2:])
            return ('', original)

        if not phones:
            # Fallback: highlight from last vowel
            for k in range(len(original)):
                if original[k].lower() in 'aeiouy':
                    return (original[:k], original[k:])
            return ('', original)

        rhyme_part = pronouncing.rhyming_part(phones)
        if not rhyme_part:
            return ('', original)

        # Count phonemes before the rhyme part
        all_phonemes = phones.split()
        rhyme_phonemes = rhyme_part.split()
        onset_count = len(all_phonemes) - len(rhyme_phonemes)

        if onset_count <= 0:
            return ('', original)

        # Map onset phonemes to approximate character positions
        # Use a heuristic: consonant phonemes ≈ 1-2 chars, vowel phonemes ≈ 1-2 chars
        # We align by finding the vowel that starts the rhyme
        # The first rhyme phoneme is always a vowel (stressed)
        # Find the corresponding vowel in the original word
        vowel_map = 'aeiouy'
        vowels_seen = 0
        target_vowel_idx = 0

        # Count vowel phonemes in onset
        for p in all_phonemes[:onset_count]:
            stripped = re.sub(r'\d', '', p)
            if stripped[0] in 'AEIOU':
                target_vowel_idx += 1

        # Find the target_vowel_idx-th vowel in the original word
        vowel_count = 0
        split_pos = 0
        for k, ch in enumerate(original.lower()):
            if ch in vowel_map:
                if vowel_count == target_vowel_idx:
                    split_pos = k
                    break
                vowel_count += 1
        else:
            # Didn't find; fall back to whole word
            return ('', original)

        if split_pos == 0:
            return ('', original)

        return (original[:split_pos], original[split_pos:])

    def _phoneme_distance(self, rp1: str, rp2: str) -> float:
        """
        Weighted edit distance between two rhyming parts.
        Vowel substitutions cost 0.5 (closer slant rhyme), consonant substitutions cost 1.0.
        Used to detect near/slant rhymes (distance <= 1).
        """
        if any(ord(c) > 127 for c in rp1 + rp2):
            # Character-level Levenshtein for Indian script endings
            m, n_p = len(rp1), len(rp2)
            if abs(m - n_p) > 1:
                return abs(m - n_p)
            dp = [[0.0] * (n_p + 1) for _ in range(m + 1)]
            for i_d in range(m + 1):
                dp[i_d][0] = float(i_d)
            for j_d in range(n_p + 1):
                dp[0][j_d] = float(j_d)
            for i_d in range(1, m + 1):
                for j_d in range(1, n_p + 1):
                    cost = 0.0 if rp1[i_d - 1] == rp2[j_d - 1] else 1.0
                    dp[i_d][j_d] = min(
                        dp[i_d - 1][j_d] + 1.0,
                        dp[i_d][j_d - 1] + 1.0,
                        dp[i_d - 1][j_d - 1] + cost
                    )
            return dp[m][n_p]

        p1 = rp1.split()
        p2 = rp2.split()
        # Strip stress digits for comparison
        p1_clean = [re.sub(r'\d', '', p) for p in p1]
        p2_clean = [re.sub(r'\d', '', p) for p in p2]

        m, n_p = len(p1_clean), len(p2_clean)
        if abs(m - n_p) > 2:
            return float(abs(m - n_p))

        _VOWELS = {'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY',
                    'IH', 'IY', 'OW', 'OY', 'UH', 'UW'}

        def _sub_cost(a: str, b: str) -> float:
            if a == b:
                return 0.0
            a_is_vowel = a in _VOWELS
            b_is_vowel = b in _VOWELS
            # Vowel↔Vowel swap = close slant (0.5)
            if a_is_vowel and b_is_vowel:
                return 0.5
            # Consonant↔Consonant swap = moderate (1.0)
            if not a_is_vowel and not b_is_vowel:
                return 1.0
            # Vowel↔Consonant swap = far (1.5)
            return 1.5

        # Weighted Levenshtein
        dp = [[0.0] * (n_p + 1) for _ in range(m + 1)]
        for i_d in range(m + 1):
            dp[i_d][0] = float(i_d)
        for j_d in range(n_p + 1):
            dp[0][j_d] = float(j_d)
        for i_d in range(1, m + 1):
            for j_d in range(1, n_p + 1):
                cost = _sub_cost(p1_clean[i_d - 1], p2_clean[j_d - 1])
                dp[i_d][j_d] = min(
                    dp[i_d - 1][j_d] + 1.0,
                    dp[i_d][j_d - 1] + 1.0,
                    dp[i_d - 1][j_d - 1] + cost
                )
        return dp[m][n_p]

    def _get_stressed_vowel(self, phones: str) -> str:
        """Extract only the primary stressed vowel phoneme (e.g., 'EY', 'AA', 'IY')."""
        if not phones:
            return ''
        for p in phones.split():
            if '1' in p:
                return re.sub(r'\d', '', p)
        # Fallback: first vowel
        for p in phones.split():
            if p[0] in 'AEIOUaeiou':
                return re.sub(r'\d', '', p)
        return ''

    def _get_consonant_frame(self, phones: str) -> str:
        """
        Extract the consonant skeleton from phonemes.
        E.g., 'L AH1 K' → 'L_K', 'S T R AO1 NG' → 'S_T_R_NG'
        """
        if not phones:
            return ''
        consonants = []
        for p in phones.split():
            stripped = re.sub(r'\d', '', p)
            if stripped and stripped[0] not in 'AEIOU':
                consonants.append(stripped)
        return '_'.join(consonants) if len(consonants) >= 2 else ''

    def _is_multi_syllable_rhyme(self, phones1: str, phones2: str) -> bool:
        """
        Check if two words share a multi-syllable rhyme (4+ trailing phonemes match for English, 2+ vowels for Indian scripts).
        E.g., 'education' / 'motivation' share 'EY1 SH AH0 N'.
        """
        is_indian = any(c.islower() for c in phones1)
        p1 = [re.sub(r'\d', '', p) for p in phones1.split()]
        p2 = [re.sub(r'\d', '', p) for p in phones2.split()]

        # Count matching trailing phonemes
        match_count = 0
        for a, b in zip(reversed(p1), reversed(p2)):
            if a == b:
                match_count += 1
            else:
                break

        if is_indian:
            return match_count >= 2
        return match_count >= 4

    def _find_alliterations(self, lines: List[str]) -> List[List[str]]:
        """Find words that alliterate in each line"""
        result = []
        for line in lines:
            words = line.split()
            if not words:
                result.append([])
                continue
                
            # Get first letters
            firsts = {}
            for word in words:
                clean = re.sub(r'[^a-z]', '', word.lower())
                if clean:
                    f = clean[0]
                    if f not in firsts:
                        firsts[f] = []
                    firsts[f].append(clean)
            
            # Keep only those with 2+ count
            line_allits = []
            for chars in firsts.values():
                if len(chars) >= 2:
                    line_allits.extend(chars)
            result.append(line_allits)
        return result
    
    def _endings_rhyme(self, e1: str, e2: str) -> bool:
        """Check if two endings rhyme"""
        if e1 == e2:
            return True
        
        # Check family matches
        for family in self.RHYME_FAMILIES + self.INDIAN_FAMILIES:
            if e1 in family and e2 in family:
                return True
        
        return False
    
    def get_density_heatmap(self, lines: List[str]) -> List[Dict]:
        """Calculate rhyme density for heatmap — returns 0-100 score + specific pair callouts."""
        result = []
        
        for line in lines:
            words = line.split()
            rhyme_count = 0
            rhyme_pairs = []
            
            for i, word in enumerate(words):
                for j in range(i + 1, len(words)):
                    other = words[j]
                    e1 = self.get_rhyme_ending(word)
                    e2 = self.get_rhyme_ending(other)
                    if e1 and e2 and self._endings_rhyme(e1, e2):
                        clean_w = re.sub(r'[^a-zA-Z]', '', word.lower())
                        clean_o = re.sub(r'[^a-zA-Z]', '', other.lower())
                        if clean_w != clean_o:
                            rhyme_count += 1
                            rhyme_pairs.append({"word_a": word, "word_b": other, "ending": e1})
            
            density = rhyme_count / max(1, len(words))
            # Scale to 0-100: 0 pairs = 0, 4+ pairs = 100
            score = min(100, int((rhyme_count / 4.0) * 100))
            
            if density > 0.5:
                color = "high"
            elif density > 0.2:
                color = "medium"
            else:
                color = "low"
            
            result.append({
                "density": density,
                "color": color,
                "score": score,
                "rhyme_pairs": rhyme_pairs,
                "pair_count": rhyme_count
            })
        
        return result
    
    def get_slang_by_category(self, category: str) -> List[str]:
        """Get slang words for a category"""
        return self.SLANG.get(category.lower(), [])
    
    def get_slang_categories(self) -> List[str]:
        """Get all slang categories"""
        return list(self.SLANG.keys())
    
    def get_rhyme_scheme_string(self, lines: List[str]) -> str:
        """
        Identify common 4-line rhyme schemes (ABAB, AABB, etc.)
        Returns the specific name of the scheme if matched, otherwise the raw pattern (e.g., 'ABCA').
        """
        if not lines:
            return ""
        
        # We only care about the last 4 lines for identifying specific stanzas
        # If fewer than 4, just return standard ABC
        target_lines = lines[-4:]
        if len(target_lines) < 4:
            return self._generate_raw_scheme(target_lines)

        endings = [self.get_rhyme_ending(line.split()[-1] if line.split() else "") for line in target_lines]
        
        # Generate generic pattern (A, B, C...)
        scheme = []
        seen = {}
        current_char = 'A'
        
        for end in endings:
            if not end:
                scheme.append('X')
                continue
                
            found = None
            for known_end, char in seen.items():
                if self._endings_rhyme(end, known_end):
                    found = char
                    break
            
            if found:
                scheme.append(found)
            else:
                scheme.append(current_char)
                seen[end] = current_char
                current_char = chr(ord(current_char) + 1)
        
        raw_pattern = "".join(scheme)
        
        # Map common patterns to user-friendly names
        patterns = {
            "AABB": "AABB (Couplets)",
            "ABAB": "ABAB (Alternating)",
            "AAAA": "AAAA (Monorhyme)",
            "XAXA": "XAXA (Simple 4-line)",
            "ABBA": "ABBA (Enclosed)",
            "AXAA": "AXAA",
            "AAXA": "AAXA",
            "AAAX": "AAAX",
            "AXXA": "AXXA"
        }
        
        # Normalize pattern to always start with A (handled by logic above), 
        # but handling 'X' requires care.
        # The above logic generates ABC... 
        # We need to map 'unrhymed' to X if the user prefers that specific notation for non-rhymes?
        # Standard notation usually allows C, D, etc. 
        # However, specifically for "XAXA", that implies line 1 and 3 DO NOT rhyme with anything.
        
        # Let's do a strict check against the requested patterns using the generated ABC form.
        # The generated form will maximize rhyme matching.
        # e.g. XAXA in standard form is ABCB (where A!=C and B=B).
        
        # Let's convert our ABC form to the user's requested "X" form if unique.
        
        # Check specific known mappings from ABC format
        if raw_pattern == "ABCB": return "XAXA" # Popular ballad meter often called this
        if raw_pattern == "ABAC": return "AXXA" # Not quite standard but fits
        
        return patterns.get(raw_pattern, raw_pattern)

    def _generate_raw_scheme(self, lines: List[str]) -> str:
        """Generate standard ABCD rhyme scheme string"""
        endings = [self.get_rhyme_ending(line.split()[-1] if line.split() else "") for line in lines]
        scheme = []
        seen = {}
        current_char = 'A'
        
        for end in endings:
            if not end:
                scheme.append('X')
                continue
            found = None
            for known_end, char in seen.items():
                if self._endings_rhyme(end, known_end):
                    found = char
                    break
            if found:
                scheme.append(found)
            else:
                scheme.append(current_char)
                seen[end] = current_char
                current_char = chr(ord(current_char) + 1)
        return "".join(scheme)

    # ── 1b: On-the-fly Compound Phrase Rhyming ─────────────────────────

    def find_onthefly_phrase_rhymes(
        self, word: str, language: str = 'en', max_results: int = 20
    ) -> List[Dict]:
        """
        Generate 2-word phrase rhymes on-the-fly by splitting CMUDict phoneme tails.
        E.g., 'orange' → 'door hinge', 'purple' → 'hurt full'.
        No database required — works purely from CMUDict pronunciations.
        """
        if language != 'en':
            return []  # CMUDict is English-only

        word_clean = re.sub(r'[^a-z]', '', word.lower())
        if not word_clean:
            return []

        phones_list = pronouncing.phones_for_word(word_clean)
        if not phones_list:
            return []

        target_phones = phones_list[0].split()
        target_len = len(target_phones)
        if target_len < 3:
            return []

        results = []
        seen = set()

        # Try splitting target phoneme sequence at each position
        for split_pos in range(2, target_len - 1):
            part_a_phones = target_phones[:split_pos]
            part_b_phones = target_phones[split_pos:]

            part_a_str = " ".join(part_a_phones)
            part_b_str = " ".join(part_b_phones)

            # Find words matching each part (strip stress for comparison)
            part_a_stripped = " ".join(re.sub(r'\d', '', p) for p in part_a_phones)
            part_b_stripped = " ".join(re.sub(r'\d', '', p) for p in part_b_phones)

            matches_a = self._find_words_by_phones(part_a_stripped, limit=8)
            matches_b = self._find_words_by_phones(part_b_stripped, limit=8)

            for wa in matches_a:
                for wb in matches_b:
                    if wa == wb or wa == word_clean or wb == word_clean:
                        continue
                    combo = f"{wa} {wb}"
                    if combo not in seen:
                        seen.add(combo)
                        results.append({
                            "phrase": combo,
                            "type": "compound",
                            "split_at": split_pos,
                            "word_count": 2
                        })

        results = results[:max_results]
        return results

    def _find_words_by_phones(self, target_stripped: str, limit: int = 8) -> List[str]:
        """Find CMUDict words whose phoneme sequence (stress-stripped) matches target."""
        matches = []
        try:
            if not pronouncing.pronunciations:
                pronouncing.init_cmu()
            for entry_word, entry_phones in pronouncing.pronunciations:
                if len(matches) >= limit:
                    break
                clean_entry = entry_word.strip().lower()
                if not clean_entry.isalpha() or len(clean_entry) < 2:
                    continue
                stripped = " ".join(re.sub(r'\d', '', p) for p in entry_phones.split())
                if stripped == target_stripped:
                    matches.append(clean_entry)
        except Exception:
            pass
        return matches

    # ── 1d: Cross-Language Rhyme Matching ──────────────────────────────

    # IPA-like normalization bridge for cross-language rhyme comparison
    _CMU_TO_IPA = {
        'AA': 'aː', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔː', 'AW': 'aʊ', 'AY': 'aɪ',
        'EH': 'ɛ', 'ER': 'ɝ', 'EY': 'eɪ', 'IH': 'ɪ', 'IY': 'iː',
        'OW': 'oʊ', 'OY': 'ɔɪ', 'UH': 'ʊ', 'UW': 'uː',
    }
    _INDIAN_TO_IPA = {
        'a': 'ʌ', 'aa': 'aː', 'i': 'ɪ', 'ii': 'iː', 'u': 'ʊ', 'uu': 'uː',
        'e': 'ɛ', 'ee': 'eɪ', 'ai': 'aɪ', 'o': 'oʊ', 'oo': 'oʊ', 'au': 'aʊ',
        'ri': 'ɝ',
    }

    def _normalize_to_ipa_key(self, vowel_seq: str, language: str) -> str:
        """Convert vowel sequence to IPA-like key for cross-language comparison."""
        if not vowel_seq:
            return ""

        parts = vowel_seq.split("-")
        ipa_parts = []

        if language == 'en':
            for p in parts:
                clean = re.sub(r'\d', '', p)
                ipa_parts.append(self._CMU_TO_IPA.get(clean, clean.lower()))
        else:  # hi, kn
            for p in parts:
                ipa_parts.append(self._INDIAN_TO_IPA.get(p.lower(), p.lower()))

        return "-".join(ipa_parts)

    async def find_cross_language_rhymes(
        self, session: 'AsyncSession', word: str,
        source_lang: str = 'en', target_lang: str = 'hi',
        max_results: int = 20
    ) -> List[Dict]:
        """
        Find rhymes across languages using IPA-bridge normalization.
        E.g., English 'fire' (AY-ER → aɪ-ɝ) matches Hinglish 'shaayar' (aa-a → aː-ʌ).
        """
        # Get source word's vowel sequence and normalize
        src_vowels, _, src_syls = self.extract_vowels(word, source_lang)
        src_ipa = self._normalize_to_ipa_key(src_vowels, source_lang)

        if not src_ipa:
            return []

        # Query target language words from DB
        query = select(MultisyllabicWord).where(
            MultisyllabicWord.language == target_lang
        ).limit(500)
        res = await session.execute(query)
        target_words = res.scalars().all()

        results = []
        for tw in target_words:
            tw_ipa = self._normalize_to_ipa_key(tw.vowel_sequence, target_lang)
            if not tw_ipa:
                continue

            # Compare IPA keys — exact match or close match
            if tw_ipa == src_ipa:
                match_type = "exact_cross"
                score = 100
            elif self._ipa_distance(src_ipa, tw_ipa) <= 1:
                match_type = "near_cross"
                score = 75
            else:
                continue

            results.append({
                "word": tw.word,
                "language": tw.language,
                "source_ipa": src_ipa,
                "target_ipa": tw_ipa,
                "match_type": match_type,
                "score": score,
                "syllable_count": tw.syllable_count,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]

    def _ipa_distance(self, ipa1: str, ipa2: str) -> int:
        """Simple Levenshtein on IPA segments."""
        p1 = ipa1.split("-")
        p2 = ipa2.split("-")
        m, n = len(p1), len(p2)
        if abs(m - n) > 1:
            return abs(m - n)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if p1[i - 1] == p2[j - 1] else 1
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
        return dp[m][n]

    # ── 6c: Phonetic Autocomplete ─────────────────────────────────────

    async def autocomplete_rhyme(
        self, session: 'AsyncSession', partial_word: str,
        prev_line_ending: str, language: str = 'en', max_results: int = 10
    ) -> List[Dict]:
        """
        Suggest words that start with `partial_word` AND rhyme with `prev_line_ending`.
        Uses vowel-sequence prefix query against MultisyllabicWord table.
        """
        if not partial_word or not prev_line_ending:
            return []

        # Get rhyme target
        target_vowels, target_key, _ = self.extract_vowels(prev_line_ending, language)
        if not target_vowels:
            return []

        partial_clean = partial_word.lower().strip()

        # Query words starting with partial AND matching vowel sequence
        from sqlalchemy import or_

        query = select(MultisyllabicWord).where(
            MultisyllabicWord.language == language,
            func.lower(MultisyllabicWord.word).startswith(partial_clean),
            or_(
                MultisyllabicWord.vowel_sequence == target_vowels,
                MultisyllabicWord.exact_rhyme_key == target_key
            )
        ).order_by(MultisyllabicWord.upvotes.desc()).limit(max_results)

        res = await session.execute(query)
        words = res.scalars().all()

        results = []
        for w in words:
            if w.word.lower() != prev_line_ending.lower():
                results.append({
                    "word": w.word,
                    "syllable_count": w.syllable_count,
                    "vowel_sequence": w.vowel_sequence,
                    "match_type": "exact" if w.exact_rhyme_key == target_key else "vowel",
                })

        return results

