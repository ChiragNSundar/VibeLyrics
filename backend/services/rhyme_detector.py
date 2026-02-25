"""
Rhyme Detection Service
Ported from Flask app with CMU dictionary and Indian language support
"""
import pronouncing
import re
from typing import List, Dict, Optional
from functools import lru_cache


class SyllableCounter:
    """Count syllables in text"""
    
    def count(self, text: str) -> int:
        """Count syllables in text"""
        words = text.lower().split()
        total = 0
        
        for word in words:
            word = re.sub(r'[^a-z]', '', word)
            if not word:
                continue
            
            # Try CMU dictionary first
            phones = pronouncing.phones_for_word(word)
            if phones:
                total += pronouncing.syllable_count(phones[0])
            else:
                # Fallback: count vowel groups
                vowels = re.findall(r'[aeiouy]+', word)
                total += max(1, len(vowels))
        
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
    
    def __init__(self):
        self.syllable_counter = SyllableCounter()
    
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
                clean = re.sub(r'[^a-z]', '', word.lower())
                if clean:
                    phones_list = pronouncing.phones_for_word(clean)
                    phones = phones_list[0] if phones_list else ''
                    rp = pronouncing.rhyming_part(phones) if phones else self._get_ending(clean)

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
                if dist == 1:
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

    def _phoneme_distance(self, rp1: str, rp2: str) -> int:
        """
        Edit distance between two rhyming parts (phoneme sequences).
        Used to detect near/slant rhymes (distance = 1).
        """
        p1 = rp1.split()
        p2 = rp2.split()
        # Strip stress digits for comparison
        p1 = [re.sub(r'\d', '', p) for p in p1]
        p2 = [re.sub(r'\d', '', p) for p in p2]

        m, n_p = len(p1), len(p2)
        if abs(m - n_p) > 1:
            return abs(m - n_p)

        # Simple Levenshtein
        dp = [[0] * (n_p + 1) for _ in range(m + 1)]
        for i_d in range(m + 1):
            dp[i_d][0] = i_d
        for j_d in range(n_p + 1):
            dp[0][j_d] = j_d
        for i_d in range(1, m + 1):
            for j_d in range(1, n_p + 1):
                cost = 0 if p1[i_d - 1] == p2[j_d - 1] else 1
                dp[i_d][j_d] = min(
                    dp[i_d - 1][j_d] + 1,
                    dp[i_d][j_d - 1] + 1,
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
            if p[0] in 'AEIOU':
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
        Check if two words share a multi-syllable rhyme (4+ trailing phonemes match).
        E.g., 'education' / 'motivation' share 'EY1 SH AH0 N'.
        """
        p1 = [re.sub(r'\d', '', p) for p in phones1.split()]
        p2 = [re.sub(r'\d', '', p) for p in phones2.split()]

        # Count matching trailing phonemes
        match_count = 0
        for a, b in zip(reversed(p1), reversed(p2)):
            if a == b:
                match_count += 1
            else:
                break

        # 4+ matching trailing phonemes = multi-syllable rhyme
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
        """Calculate rhyme density for heatmap"""
        result = []
        
        for line in lines:
            words = line.split()
            rhyme_count = 0
            
            for i, word in enumerate(words):
                for j, other in enumerate(words):
                    if i != j:
                        e1 = self.get_rhyme_ending(word)
                        e2 = self.get_rhyme_ending(other)
                        if self._endings_rhyme(e1, e2):
                            rhyme_count += 1
            
            density = rhyme_count / max(1, len(words))
            
            if density > 0.5:
                color = "high"
            elif density > 0.2:
                color = "medium"
            else:
                color = "low"
            
            result.append({"density": density, "color": color})
        
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
