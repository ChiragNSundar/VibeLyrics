"""
Indian Language Thesaurus
Synonyms, antonyms, and related words for Hindi and Kannada (romanized)
Designed to work exactly like English WordNet but for Indian languages
"""
from typing import List, Dict, Optional


class IndianThesaurus:
    """
    Thesaurus for romanized Hindi and Kannada words.
    Provides synonyms, antonyms, related words, and slang alternatives.
    """
    
    def __init__(self):
        # Hindi thesaurus (romanized)
        self.hindi_synonyms = {
            # Emotions
            "pyaar": ["mohabbat", "ishq", "prem", "sneh", "chahat"],
            "mohabbat": ["pyaar", "ishq", "prem", "ulfat"],
            "ishq": ["pyaar", "mohabbat", "prem", "junoon"],
            "khushi": ["aanand", "harsh", "sukh", "masroor"],
            "dukh": ["gham", "dard", "kasht", "peeda", "takleef"],
            "gham": ["dukh", "dard", "udaasi", "malaal"],
            "gussa": ["krodh", "ghazab", "josh", "taish"],
            "darr": ["khauf", "bhay", "dehshat", "aatank"],
            
            # People
            "dost": ["yaar", "mitra", "saheli", "rafiq", "bhai"],
            "yaar": ["dost", "bhai", "pagle", "mere"],
            "bhai": ["bhaiya", "veer", "bhrata"],
            "dushman": ["vairi", "shatru", "ripoo"],
            "aurat": ["mahila", "naari", "stree", "lady"],
            "aadmi": ["insaan", "vyakti", "manushya", "banda"],
            "banda": ["aadmi", "launda", "ladka", "bande"],
            
            # Body parts
            "dil": ["kaleja", "hriday", "jigar", "mann"],
            "aankh": ["nayan", "netra", "chashm", "nazar"],
            "haath": ["baazu", "kara", "panja"],
            "sar": ["maatha", "sir", "dimaag"],
            
            # Nature
            "raat": ["shab", "nishar", "raatri", "ratiya"],
            "din": ["divas", "roz", "subah"],
            "chaand": ["chandrama", "mahtaab", "soma"],
            "sitara": ["taara", "najm", "nakshatra"],
            "aasman": ["aakash", "gagan", "falak", "ambar"],
            "zameen": ["dharti", "bhumi", "arz"],
            "paani": ["jal", "neer", "aab"],
            "aag": ["agni", "aatish", "jwala"],
            
            # Actions
            "bolna": ["kehna", "bataana", "sunana"],
            "sunna": ["sun", "sunle", "sune"],
            "dekhna": ["dekh", "nigaah", "nazar"],
            "chalna": ["jaana", "nikalna", "badhna"],
            "aana": ["pahunchna", "aao", "aaja"],
            "jaana": ["chalna", "nikalna", "jaao"],
            "karna": ["banana", "rachna", "karo"],
            "sochna": ["vichar", "socho", "samajhna"],
            
            # Descriptors
            "accha": ["badhiya", "shandar", "behtareen", "lajawaab"],
            "bura": ["kharab", "ganda", "bekaar", "wahiyaat"],
            "sundar": ["khoobsurat", "haseen", "jameel", "pyaara"],
            "bara": ["bada", "vishaal", "azeem"],
            "chota": ["nanhi", "chhota", "nikka"],
            
            # Money/Success
            "paisa": ["rupaya", "maal", "daulat", "lakshmi"],
            "ameer": ["daulat", "maal", "raees", "dhanwan"],
            "gareeb": ["kangaal", "nirdhan", "fakeer"],
            "kaamyaabi": ["safalta", "jeet", "fatah"],
            
            # Hip-hop/Street slang
            "scene": ["maamla", "chakkar", "haal"],
            "game": ["khel", "maidan", "jung"],
            "flow": ["dhara", "bahao", "raftar"],
            "bars": ["lines", "gaaney", "lafz"],
        }
        
        self.hindi_antonyms = {
            "pyaar": ["nafrat", "dushmani"],
            "khushi": ["dukh", "gham", "udaasi"],
            "dukh": ["khushi", "aanand", "sukh"],
            "dost": ["dushman", "vairi"],
            "accha": ["bura", "kharab"],
            "bura": ["accha", "badhiya"],
            "bara": ["chota", "nanhi"],
            "chota": ["bara", "bada"],
            "raat": ["din", "subah"],
            "din": ["raat", "shab"],
            "ameer": ["gareeb", "kangaal"],
            "gareeb": ["ameer", "daulat"],
            "aana": ["jaana", "nikalna"],
            "jaana": ["aana", "rukna"],
        }
        
        # Kannada thesaurus (romanized) - EXPANDED
        self.kannada_synonyms = {
            # Pronouns (CRITICAL - these are most common)
            "naanu": ["nane", "nanu", "naane"],
            "nane": ["naanu", "nanu", "naane"],
            "nanu": ["naanu", "nane", "naane"],
            "neenu": ["nee", "neene", "ninu"],
            "nee": ["neenu", "neene", "ninu"],
            "avanu": ["aatanu", "avanige", "huduga"],
            "avalu": ["aakenu", "aavaluge", "hudugi"],
            "naavu": ["naamgalu", "naavugalu"],
            "neevu": ["neevugalu", "nimgalu"],
            "avaru": ["avarugalu", "janagalu"],
            "idu": ["ee", "ithu", "ivanu"],
            "adu": ["aa", "athu", "avanu"],
            "yenu": ["enu", "yaava", "yavudu"],
            "yaaru": ["yavaru", "yaavaru", "yavudu"],
            "elli": ["yelli", "yavalli", "aalli"],
            "yaake": ["yaakendare", "karana", "hege"],
            "hege": ["hengey", "yaava reethi", "ondu"],
            "yavaga": ["yaavattu", "yaava samaya"],
            
            # Common verbs
            "maadu": ["maadona", "maadisona", "kelasa maadu"],
            "hogi": ["hogo", "hogona", "hogadu"],
            "baa": ["baaro", "barona", "bandu"],
            "nodi": ["nodona", "nodadu", "kanu"],
            "helu": ["helona", "heladu", "cheppu"],
            "kelsu": ["kelu", "kelona", "aalisona"],
            "togo": ["togona", "tegedu", "hididu"],
            "kodu": ["kodona", "kottadu", "needu"],
            "thogo": ["thirugi", "kodu", "needu"],
            "iru": ["irona", "iddey", "irali"],
            "aagu": ["aagona", "aagadu"],
            "beku": ["bekagide", "bekaaguttey"],
            "illa": ["illave", "illadiru"],
            "ide": ["iddey", "ittu"],
            
            # Emotions
            "preeti": ["prema", "preethi", "snehaa", "mohaa", "anuraaga"],
            "prema": ["preeti", "anuraaga", "snehaa", "mohabbat"],
            "santhosha": ["khushi", "harsha", "ullasa", "aananda"],
            "dukha": ["kashta", "novu", "vyathey", "bedaru"],
            "kopaa": ["sinna", "rosaa", "ugra", "kopa"],
            "bhaya": ["dayira", "hecchu", "halliya", "hucchu"],
            "aase": ["ichche", "kaamana", "bayake"],
            
            # People  
            "guru": ["maestre", "adhyapaka", "shikshaka", "teacher"],
            "maga": ["huduga", "baalaka", "putra", "makalu"],
            "magalu": ["hudugi", "baalaki", "putri", "hennu"],
            "appa": ["thande", "pitaji", "father"],
            "amma": ["taayi", "maate", "mother"],
            "anna": ["bhaiya", "anna", "elder brother"],
            "akka": ["didi", "akka", "elder sister"],
            "tamma": ["chikka", "younger brother"],
            "tangi": ["chikki", "younger sister"],
            "snehita": ["geleya", "mitra", "friend"],
            "geleya": ["snehita", "mitra", "friend", "yaar"],
            "shatru": ["vairi", "dripu", "enemy"],
            "hendati": ["bhaama", "rani", "wife"],
            "ganda": ["pati", "swami", "husband"],
            "thala": ["boss", "leader", "nayaka"],
            "maccha": ["friend", "bro", "dost"],
            
            # Body parts
            "manasu": ["hridaya", "mana", "chitta", "dil"],
            "kannu": ["netra", "drishti", "akshi", "kanna"],
            "kai": ["hastha", "baahu", "kaigalu"],
            "tale": ["shira", "nooru", "thaley"],
            "mukha": ["modha", "chehere", "face"],
            "kivi": ["karna", "ear"],
            "moogu": ["naasika", "nose"],
            "baai": ["naalige", "baayi", "mouth"],
            
            # Nature
            "dina": ["dinaa", "haalu", "belaku", "day"],
            "raatri": ["irulu", "nisha", "night"],
            "beligge": ["morning", "udaya", "prabhata"],
            "saanje": ["evening", "sandhya"],
            "chandra": ["tingalu", "chandira", "moon"],
            "surya": ["raviya", "bhaanu", "sun"],
            "nakshatra": ["taare", "jyoti", "star"],
            "aakasha": ["gagana", "bhyoma", "nabha", "sky"],
            "bhoomi": ["nela", "dharani", "vasundhara", "earth"],
            "neeru": ["jala", "neer", "ambu", "water"],
            "benki": ["agni", "jwale", "fire"],
            "gaali": ["vayu", "wind"],
            "male": ["varsha", "rain"],
            
            # Descriptors
            "olleya": ["chennagi", "suttidey", "shreshtha", "good"],
            "kettadu": ["shobha", "ketta", "bad"],
            "sundara": ["adbhuta", "manohara", "beautiful"],
            "dodda": ["pedda", "vishala", "mahaanu", "big"],
            "chikka": ["sanna", "nannadi", "kutti", "small"],
            "hosa": ["new", "naveena", "hosu"],
            "haleyadu": ["old", "puraatana"],
            "bisi": ["hot", "ushnata"],
            "thanda": ["cold", "shaanta"],
            
            # Hip-hop/Street
            "scene": ["chakkar", "matter", "viषय"],
            "game": ["khela", "aata"],
            "style": ["moda", "fashion"],
            "swag": ["attitude", "dabang"],
        }
        
        self.kannada_antonyms = {
            "preeti": ["dvesha", "ashanthi", "kopaa"],
            "santhosha": ["dukha", "kashta", "novu"],
            "dukha": ["santhosha", "harsha", "aananda"],
            "olleya": ["kettadu", "shobha", "ketta"],
            "dodda": ["chikka", "sanna", "kutti"],
            "chikka": ["dodda", "pedda", "vishala"],
            "dina": ["raatri", "irulu"],
            "raatri": ["dina", "belaku"],
            "snehita": ["shatru", "vairi"],
            "hosa": ["haleyadu", "puraatana"],
            "bisi": ["thanda", "shaanta"],
            "baa": ["hogi", "hogadu"],
            "hogi": ["baa", "barona"],
        }
        
        # Related concepts (for both languages)
        self.related_concepts = {
            # Love/Romance cluster
            "pyaar": ["dil", "ishq", "mohabbat", "chaand", "raat", "sapna"],
            "preeti": ["manasu", "prema", "chandra", "kannu", "haadu"],
            
            # Success/Money cluster  
            "paisa": ["game", "hustle", "grind", "bread", "cheddar"],
            "kaamyaabi": ["jeet", "top", "king", "crown", "throne"],
            
            # Street/Hip-hop cluster
            "bhai": ["gang", "squad", "crew", "fam", "homies"],
            "scene": ["vibe", "mood", "setting", "spot"],
            
            # Pain/Struggle cluster
            "dukh": ["raat", "aankh", "dil", "zindagi", "safar"],
            "dard": ["ghav", "aansoo", "takleef", "mushkil"],
        }
        
        # Merge for unified lookup
        self.all_synonyms = {**self.hindi_synonyms, **self.kannada_synonyms}
        self.all_antonyms = {**self.hindi_antonyms, **self.kannada_antonyms}
    
    def get_synonyms(self, word: str, limit: int = 5) -> List[str]:
        """Get synonyms for a word"""
        word = word.lower().strip()
        synonyms = self.all_synonyms.get(word, [])
        return synonyms[:limit]
    
    def get_antonyms(self, word: str, limit: int = 3) -> List[str]:
        """Get antonyms for a word"""
        word = word.lower().strip()
        antonyms = self.all_antonyms.get(word, [])
        return antonyms[:limit]
    
    def get_related(self, word: str, limit: int = 5) -> List[str]:
        """Get related/associated words"""
        word = word.lower().strip()
        related = self.related_concepts.get(word, [])
        return related[:limit]
    
    def lookup(self, word: str) -> Dict:
        """
        Full lookup for a word - synonyms, antonyms, and related.
        Returns empty dict if word not found.
        """
        word = word.lower().strip()
        
        synonyms = self.get_synonyms(word)
        antonyms = self.get_antonyms(word)
        related = self.get_related(word)
        
        if not synonyms and not antonyms and not related:
            return {}
        
        return {
            "word": word,
            "synonyms": synonyms,
            "antonyms": antonyms,
            "related": related,
            "language": self._detect_language(word)
        }
    
    def _detect_language(self, word: str) -> str:
        """Detect if word is Hindi or Kannada"""
        if word in self.hindi_synonyms or word in self.hindi_antonyms:
            return "hindi"
        elif word in self.kannada_synonyms or word in self.kannada_antonyms:
            return "kannada"
        return "unknown"
    
    def search(self, query: str) -> List[Dict]:
        """
        Search for words matching query.
        Returns list of matching entries.
        """
        query = query.lower().strip()
        results = []
        
        for word in self.all_synonyms.keys():
            if query in word or word.startswith(query):
                results.append(self.lookup(word))
        
        return results[:10]
    
    def get_rhyming_synonyms(self, word: str, ending: str = None) -> List[str]:
        """
        Get synonyms that also rhyme (share ending sounds).
        Useful for lyric writing.
        """
        synonyms = self.get_synonyms(word, limit=10)
        
        if not ending:
            # Use last 2 characters as rhyme pattern
            ending = word[-2:] if len(word) >= 2 else word
        
        rhyming = [s for s in synonyms if s.endswith(ending) or s[-2:] == ending]
        return rhyming


# Singleton instance
_indian_thesaurus = None

def get_indian_thesaurus() -> IndianThesaurus:
    global _indian_thesaurus
    if _indian_thesaurus is None:
        _indian_thesaurus = IndianThesaurus()
    return _indian_thesaurus
