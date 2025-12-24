"""
Ultra-Detailed Thesaurus Engine
Combines WordNet, curated databases, and AI fallback for comprehensive word lookup.
Supports English, Hindi, and Kannada with rich metadata.
"""
from typing import List, Dict, Optional, Any
import re


class UltraThesaurus:
    """
    Ultra-detailed thesaurus combining:
    1. WordNet (English)
    2. Curated Indian language database
    3. Hip-hop/slang extensions
    4. AI fallback for unknown words
    """
    
    def __init__(self):
        self._init_slang_database()
        self._init_hip_hop_vocabulary()
        self._init_emotional_categories()
    
    def _init_slang_database(self):
        """Extended slang and informal vocabulary"""
        self.slang_synonyms = {
            # Money terms
            "money": ["bread", "paper", "bands", "racks", "stacks", "guap", "cheddar", "cheese", "gwop", "dough", "cash", "moolah", "bucks", "green", "scrilla"],
            "rich": ["loaded", "stacked", "balling", "paid", "wealthy", "flush", "minted", "well-off"],
            "poor": ["broke", "struggling", "down-bad", "hurting", "starving"],
            
            # People terms
            "friend": ["homie", "dawg", "bro", "fam", "gang", "squad", "crew", "ace", "bestie", "partner", "ride-or-die"],
            "enemy": ["opp", "hater", "snake", "rival", "beef", "foe"],
            "girl": ["shawty", "shorty", "ma", "queen", "wifey", "bae", "baddie", "dime"],
            "guy": ["dude", "bro", "homie", "G", "king", "dawg", "man", "fella"],
            
            # Actions
            "leave": ["dip", "bounce", "slide", "ghost", "jet", "roll out", "peace out"],
            "arrive": ["pull up", "slide through", "come through", "touch down"],
            "fight": ["scrap", "beef", "throw hands", "square up", "clash"],
            "win": ["W", "dub", "victory", "triumph", "secure the bag"],
            "lose": ["L", "take the L", "fail", "fumble", "choke"],
            
            # Emotions
            "happy": ["vibing", "lit", "hype", "feeling good", "blessed", "thriving"],
            "sad": ["down", "in my feels", "hurting", "broken", "crying inside"],
            "angry": ["heated", "tight", "pressed", "mad", "furious", "vexed"],
            "cool": ["chill", "ice cold", "smooth", "slick", "fly", "fresh", "dope"],
            
            # Quality descriptors
            "good": ["fire", "lit", "heat", "gas", "valid", "solid", "legit", "bussin", "goated"],
            "bad": ["trash", "wack", "mid", "L", "ass", "weak", "garbage"],
            "real": ["authentic", "genuine", "true", "facts", "no cap", "100", "solid"],
            "fake": ["cap", "fraud", "phony", "plastic", "sus", "snake"],
            
            # Intensity
            "very": ["hella", "mad", "crazy", "stupid", "dummy", "real", "lowkey", "highkey"],
            "a lot": ["bare", "mad", "hella", "tons", "crazy amounts"],
        }
        
        self.slang_antonyms = {
            "money": ["broke", "poverty", "struggle"],
            "rich": ["broke", "poor", "struggling"],
            "friend": ["opp", "enemy", "hater", "snake"],
            "win": ["lose", "L", "fail"],
            "good": ["bad", "trash", "wack", "mid"],
            "real": ["fake", "cap", "fraud"],
            "happy": ["sad", "down", "depressed"],
        }
    
    def _init_hip_hop_vocabulary(self):
        """Hip-hop specific vocabulary with rich synonyms"""
        self.hip_hop_terms = {
            # Rhyming/Flow
            "flow": ["cadence", "delivery", "rhythm", "style", "pocket", "groove"],
            "bars": ["lyrics", "lines", "verses", "rhymes", "punchlines", "wordplay"],
            "beat": ["instrumental", "track", "production", "sample", "loop"],
            
            # Street/Life
            "hustle": ["grind", "work", "chase", "struggle", "come up"],
            "street": ["block", "hood", "trap", "corner", "turf"],
            "trap": ["spot", "block", "corner", "bando"],
            
            # Success
            "success": ["come up", "glow up", "blow up", "make it", "win"],
            "famous": ["known", "big", "mainstream", "viral", "trending"],
            
            # Jewelry/Fashion
            "jewelry": ["ice", "drip", "bling", "chains", "rocks", "diamonds"],
            "clothes": ["drip", "fit", "threads", "gear", "wardrobe"],
            "car": ["whip", "ride", "wheels", "foreign", "slab"],
        }
    
    def _init_emotional_categories(self):
        """Emotional vocabulary organized by intensity and nuance"""
        self.emotion_spectrum = {
            "love": {
                "mild": ["like", "fond", "care", "appreciate"],
                "moderate": ["adore", "cherish", "treasure", "devoted"],
                "intense": ["passionate", "obsessed", "consumed", "crazy about"],
                "poetic": ["enamored", "smitten", "beguiled", "captivated"]
            },
            "sadness": {
                "mild": ["blue", "down", "low", "off"],
                "moderate": ["sad", "unhappy", "sorrowful", "melancholy"],
                "intense": ["depressed", "devastated", "heartbroken", "crushed"],
                "poetic": ["forlorn", "desolate", "bereft", "wistful"]
            },
            "anger": {
                "mild": ["annoyed", "irritated", "bothered", "peeved"],
                "moderate": ["angry", "mad", "upset", "heated"],
                "intense": ["furious", "enraged", "livid", "seething"],
                "poetic": ["wrathful", "incensed", "indignant"]
            },
            "fear": {
                "mild": ["nervous", "uneasy", "anxious", "worried"],
                "moderate": ["afraid", "scared", "fearful", "frightened"],
                "intense": ["terrified", "petrified", "panicked", "horror"],
                "poetic": ["dread", "trepidation", "foreboding"]
            },
            "joy": {
                "mild": ["pleased", "content", "satisfied", "glad"],
                "moderate": ["happy", "joyful", "cheerful", "delighted"],
                "intense": ["ecstatic", "elated", "overjoyed", "euphoric"],
                "poetic": ["blissful", "rapturous", "jubilant", "exultant"]
            }
        }
    
    def lookup(self, word: str, include_ai: bool = True) -> Dict[str, Any]:
        """
        Ultra-detailed lookup combining all sources.
        
        Returns:
        - synonyms (with categories)
        - antonyms
        - related_words
        - emotional_variants (if applicable)
        - slang_alternatives
        - hip_hop_terms (if applicable)
        - usage_examples
        - rhyming_alternatives
        """
        word = word.lower().strip()
        result = {
            "word": word,
            "sources_used": [],
            "synonyms": [],
            "antonyms": [],
            "related": [],
            "categories": {}
        }
        
        # 1. Try WordNet for English
        wordnet_result = self._wordnet_lookup(word)
        if wordnet_result["found"]:
            result["synonyms"].extend(wordnet_result["synonyms"])
            result["antonyms"].extend(wordnet_result["antonyms"])
            result["categories"]["formal"] = wordnet_result.get("formal", [])
            result["categories"]["definitions"] = wordnet_result.get("definitions", [])
            result["sources_used"].append("wordnet")
        
        # 2. Add slang alternatives
        if word in self.slang_synonyms:
            result["categories"]["slang"] = self.slang_synonyms[word]
            result["synonyms"].extend(self.slang_synonyms[word])
            result["sources_used"].append("slang_db")
        
        if word in self.slang_antonyms:
            result["antonyms"].extend(self.slang_antonyms[word])
        
        # 3. Add hip-hop specific terms
        if word in self.hip_hop_terms:
            result["categories"]["hip_hop"] = self.hip_hop_terms[word]
            result["synonyms"].extend(self.hip_hop_terms[word])
            result["sources_used"].append("hip_hop_db")
        
        # 4. Check for emotional word with spectrum
        for emotion, spectrum in self.emotion_spectrum.items():
            all_emotion_words = []
            for intensity_words in spectrum.values():
                all_emotion_words.extend(intensity_words)
            
            if word in all_emotion_words or word == emotion:
                result["categories"]["emotional_spectrum"] = spectrum
                result["sources_used"].append("emotion_db")
                break
        
        # 5. Try Indian thesaurus
        indian_result = self._indian_lookup(word)
        if indian_result:
            result["synonyms"].extend(indian_result.get("synonyms", []))
            result["antonyms"].extend(indian_result.get("antonyms", []))
            result["related"].extend(indian_result.get("related", []))
            result["categories"]["indian_language"] = indian_result
            result["sources_used"].append("indian_thesaurus")
        
        # 6. AI fallback if nothing found or user wants expanded results
        if include_ai and (not result["synonyms"] or len(result["synonyms"]) < 5):
            ai_result = self._ai_expand(word, existing=result["synonyms"])
            if ai_result:
                result["categories"]["ai_generated"] = ai_result
                result["synonyms"].extend(ai_result.get("synonyms", []))
                result["related"].extend(ai_result.get("related", []))
                result["sources_used"].append("ai")
        
        # Deduplicate
        result["synonyms"] = list(dict.fromkeys(result["synonyms"]))
        result["antonyms"] = list(dict.fromkeys(result["antonyms"]))
        result["related"] = list(dict.fromkeys(result["related"]))
        
        return result
    
    def _wordnet_lookup(self, word: str) -> Dict:
        """Enhanced WordNet lookup with definitions and examples"""
        try:
            from nltk.corpus import wordnet
            
            synsets = wordnet.synsets(word)
            if not synsets:
                return {"found": False}
            
            synonyms = set()
            antonyms = set()
            definitions = []
            examples = []
            
            for syn in synsets[:5]:  # Limit to first 5 meanings
                # Get synonyms
                for lemma in syn.lemmas():
                    name = lemma.name().replace('_', ' ')
                    if name.lower() != word:
                        synonyms.add(name)
                    
                    # Get antonyms
                    for ant in lemma.antonyms():
                        antonyms.add(ant.name().replace('_', ' '))
                
                # Get definition
                definitions.append({
                    "pos": syn.pos(),
                    "definition": syn.definition(),
                    "examples": syn.examples()[:2]
                })
            
            # Get hypernyms and hyponyms for related words
            related = set()
            for syn in synsets[:3]:
                for hyper in syn.hypernyms():
                    for lemma in hyper.lemmas():
                        related.add(lemma.name().replace('_', ' '))
                for hypo in syn.hyponyms()[:5]:
                    for lemma in hypo.lemmas():
                        related.add(lemma.name().replace('_', ' '))
            
            return {
                "found": True,
                "synonyms": list(synonyms)[:20],
                "antonyms": list(antonyms)[:10],
                "formal": list(synonyms)[:10],
                "related": list(related)[:10],
                "definitions": definitions[:3]
            }
        except Exception:
            return {"found": False}
    
    def _indian_lookup(self, word: str) -> Optional[Dict]:
        """Lookup in Indian thesaurus"""
        try:
            from app.analysis.indian_thesaurus import get_indian_thesaurus
            thesaurus = get_indian_thesaurus()
            return thesaurus.lookup(word)
        except Exception:
            return None
    
    def _ai_expand(self, word: str, existing: List[str] = None) -> Optional[Dict]:
        """Use AI to expand vocabulary for unknown words"""
        try:
            from app.ai import get_provider
            from app.models import UserProfile
            
            profile = UserProfile.get_or_create_default()
            provider = get_provider(profile.preferred_provider)
            
            existing_str = ", ".join(existing[:5]) if existing else "none found"
            
            prompt = f"""Give me a detailed thesaurus entry for the word "{word}".

Existing synonyms found: {existing_str}

Provide ONLY a JSON response with this exact structure:
{{
    "synonyms": ["word1", "word2", "word3", ...],  // 5-10 synonyms
    "antonyms": ["word1", "word2"],  // 2-5 antonyms
    "related": ["word1", "word2", "word3"],  // 3-5 related concepts
    "slang": ["word1", "word2"],  // 2-3 slang/informal alternatives
    "formal": ["word1", "word2"],  // 2-3 formal alternatives
    "usage_note": "brief note about usage"
}}

If the word is Hindi/Kannada (romanized), provide synonyms in the same language.
Return ONLY the JSON, no explanation."""

            response = provider.generate_simple(prompt, max_tokens=300)
            
            # Parse JSON from response
            import json
            # Find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data
            
            return None
        except Exception:
            return None
    
    def get_rhyming_synonyms(self, word: str) -> List[str]:
        """Get synonyms that also rhyme with the original word"""
        lookup = self.lookup(word, include_ai=False)
        synonyms = lookup.get("synonyms", [])
        
        # Get rhyme pattern
        ending = word[-2:] if len(word) >= 2 else word
        
        rhyming = []
        for syn in synonyms:
            if syn.endswith(ending) or self._sounds_similar(word, syn):
                rhyming.append(syn)
        
        return rhyming
    
    def _sounds_similar(self, word1: str, word2: str) -> bool:
        """Check if two words sound similar (basic phonetic matching)"""
        # Simple vowel pattern matching
        vowels1 = re.sub(r'[^aeiou]', '', word1.lower())
        vowels2 = re.sub(r'[^aeiou]', '', word2.lower())
        
        if len(vowels1) >= 2 and len(vowels2) >= 2:
            return vowels1[-2:] == vowels2[-2:]
        
        return False
    
    def get_by_intensity(self, emotion: str, intensity: str = "moderate") -> List[str]:
        """Get emotion words by intensity level"""
        if emotion in self.emotion_spectrum:
            return self.emotion_spectrum[emotion].get(intensity, [])
        return []


# Singleton instance
_ultra_thesaurus = None

def get_ultra_thesaurus() -> UltraThesaurus:
    global _ultra_thesaurus
    if _ultra_thesaurus is None:
        _ultra_thesaurus = UltraThesaurus()
    return _ultra_thesaurus
