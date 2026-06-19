"""
Learning System Services
- Style extraction
- Vocabulary management
- User preference learning
"""
import json
import os
import re
from typing import Dict, List, Set, Optional
from collections import Counter
from pathlib import Path


class StyleExtractor:
    """Extract and learn user's writing style"""
    
    DATA_FILE = "data/user_style.json"
    
    def __init__(self):
        self.style_data = self._load_style()
    
    def _load_style(self) -> Dict:
        """Load style data from file"""
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return self._get_default_style()
    
    def _get_default_style(self) -> Dict:
        """Default style profile"""
        return {
            "vocabulary": {
                "favorite_words": [],
                "favorite_phrases": [],
                "avoided_words": [],
                "slang_preference": "moderate"
            },
            "structure": {
                "avg_line_length": 8,
                "preferred_sections": ["Verse", "Chorus", "Bridge"]
            },
            "rhyme": {
                "scheme_preference": "AABB",
                "internal_rhyme_frequency": "moderate"
            },
            "themes": {
                "preferred": [],
                "explored": []
            }
        }
    
    def save_style(self):
        """Save style data"""
        os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)
        with open(self.DATA_FILE, 'w') as f:
            json.dump(self.style_data, f, indent=2)

    def reset(self):
        """Wipe all learned style data and reset to default."""
        self.style_data = self._get_default_style()
        self.save_style()
    
    def _extract_ngrams(self, lines: List[str], n: int) -> List[str]:
        """Extract word n-grams from lines."""
        ngrams = []
        for line in lines:
            words = [w.lower().strip(".,!?;:'\"") for w in line.split() if w.strip(".,!?;:'\"")]
            if len(words) >= n:
                for i in range(len(words) - n + 1):
                    ngrams.append(" ".join(words[i:i+n]))
        return ngrams

    def analyze_lines(self, lines: List[str]) -> Dict:
        """Analyze lines to extract style patterns"""
        if not lines:
            return {}
        
        words = []
        for line in lines:
            words.extend(w.lower().strip(".,!?;:'\"") for w in line.split() if w.strip(".,!?;:'\""))
        
        # Word frequency
        word_freq = Counter(words)
        common_words = word_freq.most_common(10)
        
        # Bigrams & Trigrams
        bigrams = self._extract_ngrams(lines, 2)
        trigrams = self._extract_ngrams(lines, 3)
        common_bigrams = [phrase for phrase, count in Counter(bigrams).most_common(5)]
        common_trigrams = [phrase for phrase, count in Counter(trigrams).most_common(5)]
        
        # Average line length
        avg_length = sum(len(line.split()) for line in lines) / len(lines)
        
        return {
            "common_words": [w for w, c in common_words],
            "avg_line_length": round(avg_length, 1),
            "total_lines": len(lines),
            "unique_words": len(set(words)),
            "common_bigrams": common_bigrams,
            "common_trigrams": common_trigrams
        }
    
    def learn_from_session(self, lines: List[str]):
        """Update style from a writing session"""
        analysis = self.analyze_lines(lines)
        if not analysis:
            return
        
        # Update average line length
        current_avg = self.style_data["structure"]["avg_line_length"]
        new_avg = analysis.get("avg_line_length", current_avg)
        self.style_data["structure"]["avg_line_length"] = round(
            (current_avg + new_avg) / 2, 1
        )

        # Track common words as potential favorites
        common = analysis.get("common_words", [])
        stop_words = {"i", "the", "a", "an", "is", "was", "are", "in", "on", "to", "and", "of", "my", "me", "it", "you", "your", "we", "they", "that", "this"}
        for word in common:
            if word not in stop_words and len(word) > 3:
                fav = self.style_data["vocabulary"]["favorite_words"]
                if word not in fav:
                    fav.append(word)
                    self.style_data["vocabulary"]["favorite_words"] = fav[-50:]
        
        # Track common phrases (bigrams/trigrams) as potential favorites
        fav_phrases = self.style_data["vocabulary"].setdefault("favorite_phrases", [])
        for phrase in analysis.get("common_bigrams", []) + analysis.get("common_trigrams", []):
            if phrase not in fav_phrases:
                fav_phrases.append(phrase)
        self.style_data["vocabulary"]["favorite_phrases"] = fav_phrases[-30:]

        self.save_style()

    def learn_from_journal(self, journal_entries: List[Dict]):
        """
        Continuously learn from journal entries.
        Extracts mood patterns and recurring keywords to inform AI suggestions.
        """
        if not journal_entries:
            return

        moods = []
        keywords = []
        for entry in journal_entries:
            content = entry.get("content", "") if isinstance(entry, dict) else str(entry)
            mood = entry.get("mood", "") if isinstance(entry, dict) else ""
            if mood:
                moods.append(mood.lower())
            # Extract meaningful keywords
            words = content.lower().split()
            stop_words = {"i", "the", "a", "an", "is", "was", "are", "in", "on", "to",
                         "and", "of", "my", "me", "it", "you", "your", "we", "they",
                         "that", "this", "but", "for", "with", "have", "had", "been",
                         "just", "about", "like", "not", "so", "at", "from", "do"}
            meaningful = [w.strip(".,!?;:'\"") for w in words
                         if w.strip(".,!?;:'\"") not in stop_words and len(w) > 3]
            keywords.extend(meaningful)

        # Store mood tendency
        if moods:
            mood_freq = Counter(moods)
            dominant_mood = mood_freq.most_common(1)[0][0]
            self.style_data.setdefault("journal", {})
            self.style_data["journal"]["dominant_mood"] = dominant_mood
            self.style_data["journal"]["mood_history"] = moods[:20]

        # Store recurring keywords
        if keywords:
            keyword_freq = Counter(keywords)
            top_keywords = [w for w, _ in keyword_freq.most_common(15)]
            self.style_data.setdefault("journal", {})
            self.style_data["journal"]["recurring_keywords"] = top_keywords

        self.save_style()
    
    def get_style_summary(self) -> Dict:
        """Get summary of learned style including journal insights"""
        summary = {
            "vocabulary_size": len(self.style_data["vocabulary"]["favorite_words"]),
            "avg_line_length": self.style_data["structure"]["avg_line_length"],
            "preferred_themes": self.style_data["themes"]["preferred"][:5],
            "rhyme_preference": self.style_data["rhyme"]["scheme_preference"],
        }
        journal = self.style_data.get("journal", {})
        if journal.get("dominant_mood"):
            summary["mood_tendency"] = journal["dominant_mood"]
        if journal.get("recurring_keywords"):
            summary["journal_keywords"] = journal["recurring_keywords"][:10]
        return summary
    
    def update_preference(self, key: str, value):
        """Update a specific preference"""
        if key == "preferred_provider":
            pass  # Handled by settings
        elif key == "default_bpm":
            pass  # Handled by settings
        else:
            # Generic update
            pass
        self.save_style()
    
    def add_preferred_theme(self, theme: str):
        """Add a preferred theme"""
        themes = self.style_data["themes"]["preferred"]
        if theme not in themes:
            themes.append(theme)
            self.save_style()


class VocabularyManager:
    """Manage user's vocabulary preferences"""
    
    DATA_FILE = "data/vocabulary.json"
    
    def __init__(self):
        self.favorite_words: Set[str] = set()
        self.favorite_slangs: Set[str] = set()
        self.avoided_words: Set[str] = set()
        self.word_frequency: Counter = Counter()
        self._load_vocabulary()
    
    def _load_vocabulary(self):
        """Load vocabulary from file"""
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.favorite_words = set(data.get("favorites", []))
                    self.favorite_slangs = set(data.get("slangs", []))
                    self.avoided_words = set(data.get("avoided", []))
                    self.word_frequency = Counter(data.get("frequency", {}))
            except Exception:
                pass
    
    def _save_vocabulary(self):
        """Save vocabulary to file"""
        os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)
        data = {
            "favorites": list(self.favorite_words),
            "slangs": list(self.favorite_slangs),
            "avoided": list(self.avoided_words),
            "frequency": dict(self.word_frequency.most_common(500))
        }
        with open(self.DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_favorite(self, word: str, is_slang: bool = False):
        """Add a favorite word"""
        word = word.lower().strip()
        if is_slang:
            self.favorite_slangs.add(word)
        else:
            self.favorite_words.add(word)
        self._save_vocabulary()
    
    def add_avoided(self, word: str):
        """Add an avoided word"""
        self.avoided_words.add(word.lower().strip())
        self._save_vocabulary()
    
    def remove_favorite(self, word: str):
        """Remove from favorites"""
        word = word.lower().strip()
        self.favorite_words.discard(word)
        self.favorite_slangs.discard(word)
        self._save_vocabulary()
    
    def remove_avoided(self, word: str):
        """Remove from avoided"""
        self.avoided_words.discard(word.lower().strip())
        self._save_vocabulary()
    
    def track_usage(self, words: List[str]):
        """Track word usage"""
        for word in words:
            word = word.lower().strip()
            if len(word) > 2:
                self.word_frequency[word] += 1
        self._save_vocabulary()

    def track_co_occurrences(self, lines: List[str]):
        """Track which words appear together in the same line for the brain map."""
        co_file = "data/co_occurrences.json"
        # Load existing
        co_data: Dict[str, Dict[str, int]] = {}
        if os.path.exists(co_file):
            try:
                with open(co_file, 'r') as f:
                    co_data = json.load(f)
            except Exception:
                pass

        stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to",
                      "for", "of", "and", "or", "but", "not", "it", "its", "my", "your",
                      "i", "me", "you", "he", "she", "we", "they", "this", "that", "with"}

        for line in lines:
            words = [w.lower().strip() for w in line.split() if len(w.strip()) > 2]
            words = [w for w in words if w not in stopwords and w.isalpha()]
            # Only care about unique words per line
            unique = list(set(words))
            for i in range(len(unique)):
                for j in range(i + 1, len(unique)):
                    w1, w2 = sorted([unique[i], unique[j]])
                    if w1 not in co_data:
                        co_data[w1] = {}
                    co_data[w1][w2] = co_data[w1].get(w2, 0) + 1

        os.makedirs(os.path.dirname(co_file), exist_ok=True)
        with open(co_file, 'w') as f:
            json.dump(co_data, f)

    def cluster_brain_map(self, brain_data: Dict) -> Dict:
        """
        Run label propagation on the nodes and links to identify community clusters.
        Modifies and returns brain_data with 'cluster_id' and 'cluster_label' on each node.
        """
        nodes = brain_data.get("nodes", [])
        links = brain_data.get("links", [])
        
        if not nodes:
            return brain_data
            
        # 1. Initialize labels: each node has its own label (its ID)
        labels = {node["id"]: node["id"] for node in nodes}
        node_freqs = {node["id"]: node.get("frequency", 1) for node in nodes}
        
        # Build adjacency list
        adj = {node["id"]: [] for node in nodes}
        for link in links:
            src = link["source"]
            tgt = link["target"]
            val = link.get("value", 1)
            if src in adj and tgt in adj:
                adj[src].append((tgt, val))
                adj[tgt].append((src, val))
                
        # 2. Run label propagation (5 iterations)
        import random
        for _ in range(5):
            shuffled_nodes = list(labels.keys())
            random.shuffle(shuffled_nodes)
            for node_id in shuffled_nodes:
                neighbors = adj[node_id]
                if not neighbors:
                    continue
                label_weights = {}
                for neighbor_id, weight in neighbors:
                    neigh_label = labels[neighbor_id]
                    label_weights[neigh_label] = label_weights.get(neigh_label, 0) + weight
                if label_weights:
                    max_weight = max(label_weights.values())
                    best_labels = [lbl for lbl, w in label_weights.items() if w == max_weight]
                    if labels[node_id] in best_labels:
                        labels[node_id] = labels[node_id]
                    else:
                        labels[node_id] = random.choice(best_labels)
                        
        # 3. Assign cluster IDs and labels
        clusters = {}
        for node_id, label in labels.items():
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(node_id)
            
        label_to_cluster_id = {}
        cluster_labels = {}
        for idx, (label, member_ids) in enumerate(clusters.items()):
            label_to_cluster_id[label] = idx
            best_node = max(member_ids, key=lambda nid: node_freqs.get(nid, 0))
            cluster_labels[label] = best_node.upper()
            
        # 4. Update the nodes in brain_data
        for node in nodes:
            node_id = node["id"]
            node_label = labels[node_id]
            node["cluster_id"] = label_to_cluster_id[node_label]
            node["cluster_label"] = cluster_labels[node_label]
            
        return brain_data

    def get_brain_map_data(self) -> Dict:
        """Generate nodes and links for the interactive brain map force graph."""
        nodes = []
        links = []
        node_ids = set()

        # Build nodes from top vocabulary
        top_words = self.word_frequency.most_common(60)
        for word, freq in top_words:
            category = "signature"
            if word in self.favorite_slangs:
                category = "slang"
            elif word in self.avoided_words:
                category = "avoided"
            elif word in self.favorite_words:
                category = "favorite"

            nodes.append({
                "id": word,
                "val": max(2, min(20, freq // 2)),
                "category": category,
                "frequency": freq
            })
            node_ids.add(word)

        # Build links from co-occurrences
        co_file = "data/co_occurrences.json"
        if os.path.exists(co_file):
            try:
                with open(co_file, 'r') as f:
                    co_data = json.load(f)
                for w1, connections in co_data.items():
                    if w1 in node_ids:
                        for w2, strength in connections.items():
                            if w2 in node_ids and strength >= 2:
                                links.append({
                                    "source": w1,
                                    "target": w2,
                                    "value": min(5, strength)
                                })
            except Exception:
                pass

        data = {"nodes": nodes, "links": links}
        return self.cluster_brain_map(data)
    
    def get_vocabulary_context(self) -> Dict:
        """Get vocabulary context for AI prompts"""
        return {
            "favorites": list(self.favorite_words)[:20],
            "slangs": list(self.favorite_slangs)[:10],
            "avoided": list(self.avoided_words)[:10],
            "most_used": [w for w, c in self.word_frequency.most_common(20)]
        }

    def reset(self):
        """Wipe all tracked vocabulary completely."""
        self.favorite_words.clear()
        self.favorite_slangs.clear()
        self.avoided_words.clear()
        self.word_frequency.clear()
        if os.path.exists(self.DATA_FILE):
            os.remove(self.DATA_FILE)
        self._save_vocabulary()


class CorrectionTracker:
    """Track user corrections to AI suggestions"""
    
    DATA_FILE = "data/corrections.json"
    
    def __init__(self):
        self.corrections: List[Dict] = []
        self._load_corrections()
    
    def _load_corrections(self):
        """Load corrections from file"""
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r') as f:
                    self.corrections = json.load(f)
            except Exception:
                pass
    
    def _save_corrections(self):
        """Save corrections"""
        os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)
        with open(self.DATA_FILE, 'w') as f:
            json.dump(self.corrections[-100:], f, indent=2)  # Keep last 100
    
    def track_correction(self, original: str, corrected: str):
        """Track a correction"""
        self.corrections.append({
            "original": original,
            "corrected": corrected,
            "diff_length": len(corrected) - len(original)
        })
        self._save_corrections()
    
    def get_correction_insights(self) -> Dict:
        """Get insights from corrections"""
        if not self.corrections:
            return {"total": 0, "avg_change": 0}
        
        total = len(self.corrections)
        avg_change = sum(c["diff_length"] for c in self.corrections) / total
        
        return {
            "total": total,
            "avg_change": round(avg_change, 1),
            "tends_to": "lengthen" if avg_change > 0 else "shorten"
        }


class ClicheDetector:
    """Detect overused hip-hop clichés and cross-reference avoided words with creative refactoring."""

    CLICHE_DICT = {
        "money on my mind": {
            "category": "wealth",
            "alternatives": ["digits in my focus", "ledger in my cortex", "wealth in my thoughts"]
        },
        "ride or die": {
            "category": "loyalty",
            "alternatives": ["loyal to the asphalt", "down to the final line", "shielding each other's path"]
        },
        "started from the bottom": {
            "category": "struggle",
            "alternatives": ["climbed from the concrete", "sprouted from the basement", "ascended from the street levels"]
        },
        "make it rain": {
            "category": "flexing",
            "alternatives": ["showering the venue", "cascading currency", "dispersing the wealth"]
        },
        "spit fire": {
            "category": "lyrics",
            "alternatives": ["discharge heat", "ignite the diaphragm", "vent volcanic rhymes"]
        },
        "die rich": {
            "category": "wealth",
            "alternatives": ["depart in luxury", "exit in gold sheets", "close the final ledger in surplus"]
        },
        "cold as ice": {
            "category": "emotion",
            "alternatives": ["glacial temperament", "frostbitten touch", "sub-zero flow"]
        },
        "streets are watching": {
            "category": "danger",
            "alternatives": ["pavement keeps count", "asphalt holds eyes", "concrete observes"]
        },
        "clock is ticking": {
            "category": "time",
            "alternatives": ["hourglass is draining", "seconds are shaving away", "tempus is pressing"]
        },
        "chasing dreams": {
            "category": "ambition",
            "alternatives": ["hunting visions", "shadowing ideals", "pursuing the eclipse"]
        },
        "on my grind": {
            "category": "hustle",
            "alternatives": ["milling the gears", "carving my path", "sanding down the hours"]
        },
        "no pain no gain": {
            "category": "effort",
            "alternatives": ["scar tissue turns to muscle", "toil seeds the harvest", "struggle pays dividends"]
        },
        "sky's the limit": {
            "category": "limitless",
            "alternatives": ["troposphere is just the doorway", "orbit is the start line", "boundless trajectory"]
        },
        "fake friends": {
            "category": "loyalty",
            "alternatives": ["hologram alliances", "synthetic smiles", "cardboard companions"]
        },
        "snakes in the grass": {
            "category": "danger",
            "alternatives": ["vipers in the lawn", "hidden fangs", "venomous stalks"]
        },
        "kill the game": {
            "category": "triumph",
            "alternatives": ["dethrone the industry", "flatline the competition", "lay the sector to rest"]
        },
        "watch your back": {
            "category": "danger",
            "alternatives": ["guard your blindside", "keep your rear view clear", "shield the spine"]
        },
        "trust no one": {
            "category": "loyalty",
            "alternatives": ["verify every signature", "keep the inner circle zero", "doubt every shadow"]
        },
        "game over": {
            "category": "end",
            "alternatives": ["curtain drop", "final whistle", "flatline state"]
        },
        "out of my mind": {
            "category": "madness",
            "alternatives": ["cortex fractured", "thoughts displaced", "sanity unanchored"]
        },
        "turning the page": {
            "category": "change",
            "alternatives": ["flipping the chapter", "shifting the narrative", "unrolling new parchment"]
        },
        "point of no return": {
            "category": "inevitable",
            "alternatives": ["event horizon reached", "bridges fully burned", "rubicon crossed"]
        },
        "in the fast lane": {
            "category": "lifestyle",
            "alternatives": ["rapid velocity pace", "accelerated lane", "high-tempo cruise"]
        },
        "stacking paper": {
            "category": "wealth",
            "alternatives": ["piling up dividends", "storing the revenue", "scaling the currency"]
        },
        "running the game": {
            "category": "triumph",
            "alternatives": ["piloting the industry", "directing the playbook", "governing the field"]
        },
        "putting in work": {
            "category": "effort",
            "alternatives": ["investing the sweat", "logging heavy shifts", "shaping the craftsmanship"]
        },
        "live my life": {
            "category": "lifestyle",
            "alternatives": ["write my own rules", "carve my path", "navigate my timeline"]
        },
        "get the money": {
            "category": "wealth",
            "alternatives": ["secure the asset", "pocket the dividend", "intercept the revenue"]
        },
        "only god can judge me": {
            "category": "attitude",
            "alternatives": ["immune to human juries", "accountable to the cosmos", "standing before the high bench"]
        },
        "real talk": {
            "category": "attitude",
            "alternatives": ["unvarnished truth", "naked vocabulary", "candid report"]
        },
        "day one": {
            "category": "loyalty",
            "alternatives": ["since the foundation", "since page single-digit", "original roster"]
        },
        "hustle hard": {
            "category": "hustle",
            "alternatives": ["grind relentlessly", "labouring heavy hours", "chafing at the wheel"]
        },
        "living the dream": {
            "category": "lifestyle",
            "alternatives": ["manifesting visions", "floating in reality", "dwelling in my aspiration"]
        },
        "hustle and flow": {
            "category": "lyrics",
            "alternatives": ["rhythm and labor", "sweat and cadence", "workmanship and delivery"]
        },
        "pay the price": {
            "category": "effort",
            "alternatives": ["bear the invoice", "settle the toll", "absorb the cost"]
        },
        "stack it to the ceiling": {
            "category": "wealth",
            "alternatives": ["pile it roof-high", "climb the mountain of paper", "vertical revenue"]
        },
        "haters gonna hate": {
            "category": "attitude",
            "alternatives": ["detractors stay active", "cynics keep talking", "critics run their course"]
        },
        "born to win": {
            "category": "triumph",
            "alternatives": ["victory pre-programmed", "destined for the crown", "predetermined champion"]
        },
        "talk is cheap": {
            "category": "attitude",
            "alternatives": ["words are draft paper", "speech carries no tax", "claims cost nothing"]
        },
        "money talks": {
            "category": "wealth",
            "alternatives": ["capital speaks volumes", "currency decides the vote", "cash commands attention"]
        },
        "ball till i fall": {
            "category": "lifestyle",
            "alternatives": ["flex until the curtain", "run the court until fatigue", "limitless flex"]
        },
        "get rich or die trying": {
            "category": "ambition",
            "alternatives": ["wealth or final breath", "abundance or flatline", "ledger full or heartbeat zero"]
        },
        "ride the wave": {
            "category": "lifestyle",
            "alternatives": ["cruise the crest", "navigate the momentum", "glide the surge"]
        },
        "top of the world": {
            "category": "triumph",
            "alternatives": ["zenith perspective", "roof of the globe", "highest elevation"]
        },
        "king of the castle": {
            "category": "triumph",
            "alternatives": ["sovereign of the sector", "monarch on the peak", "crown holder"]
        },
        "on the block": {
            "category": "danger",
            "alternatives": ["corners of the concrete", "under the grid", "asphalt outpost"]
        },
        "trap house": {
            "category": "danger",
            "alternatives": ["clandestine depot", "operations hub", "the concrete cabin"]
        },
        "living fast": {
            "category": "lifestyle",
            "alternatives": ["rapid pace", "high-velocity days", "quickening the timeline"]
        },
        "no cap": {
            "category": "attitude",
            "alternatives": ["unvarnished truth", "no fabrication", "sincere facts"]
        },
        "drip too hard": {
            "category": "flexing",
            "alternatives": ["excessive aesthetic", "overflowing style", "visual overload"]
        },
        "make it out": {
            "category": "struggle",
            "alternatives": ["breach the boundary", "cross the border wall", "escape the gravitational pull"]
        },
        "started with a dream": {
            "category": "ambition",
            "alternatives": ["sparked from a vision", "originated as a thought", "seeded in a dreamscape"]
        },
        "behind bars": {
            "category": "danger",
            "alternatives": ["inside the steel cage", "confined to coordinates", "iron shadows"]
        },
        "all about the money": {
            "category": "wealth",
            "alternatives": ["digit-centric", "exclusively cash-oriented", "currency-focused"]
        },
        "count my blessings": {
            "category": "attitude",
            "alternatives": ["tally the positives", "log the fortunes", "audit my gifts"]
        },
        "stay true": {
            "category": "loyalty",
            "alternatives": ["maintain loyalty", "preserve the origin", "anchor your character"]
        },
        "blood sweat and tears": {
            "category": "effort",
            "alternatives": ["vital fluids and labor", "exertion of life", "salty sweat and toil"]
        },
        "road to success": {
            "category": "ambition",
            "alternatives": ["pathway of achievement", "highway to the crown", "corridor of triumph"]
        },
        "keep it real": {
            "category": "attitude",
            "alternatives": ["stay transparent", "refuse the synthetic", "project the raw copy"]
        },
        "built to last": {
            "category": "triumph",
            "alternatives": ["engineered for endurance", "framed for the decades", "indestructible design"]
        },
        "hard knock life": {
            "category": "struggle",
            "alternatives": ["pathway of friction", "abrasive chronology", "difficult environment"]
        },
        "ain't no love": {
            "category": "danger",
            "alternatives": ["affection is zero", "zero warmth on the street", "absence of care"]
        },
        "another day another dollar": {
            "category": "lifestyle",
            "alternatives": ["routine shift for currency", "iterating the grind", "daily cycle of income"]
        },
        "back in the day": {
            "category": "time",
            "alternatives": ["chapters ago", "in the archival years", "history pages back"]
        },
        "checks on checks": {
            "category": "wealth",
            "alternatives": ["stacked accounts", "ledger confirmations", "recurrent payrolls"]
        },
        "racks on racks": {
            "category": "wealth",
            "alternatives": ["stacks of thousands", "cash towers", "boundless vaults"]
        },
        "roll the dice": {
            "category": "danger",
            "alternatives": ["toss the cubes", "court the probability", "trigger the gamble"]
        },
        "take a chance": {
            "category": "ambition",
            "alternatives": ["embrace the hazard", "leap the chasm", "gamble on the outcomes"]
        },
        "watch your back": {
            "category": "danger",
            "alternatives": ["guard the blindspot", "frequent the rear mirror", "secure the spine"]
        },
        "trust no one": {
            "category": "loyalty",
            "alternatives": ["verify all signatures", "suspicious of shadows", "keep coordinates private"]
        },
        "out of bounds": {
            "category": "danger",
            "alternatives": ["breaching lines", "outside safety grids", "transgressing parameters"]
        },
        "make a name": {
            "category": "ambition",
            "alternatives": ["engrave your moniker", "carve the nameplate", "stamp your presence"]
        },
        "live and learn": {
            "category": "lifestyle",
            "alternatives": ["survive to download lessons", "experience converts to wisdom", "logging the errors"]
        },
        "do or die": {
            "category": "effort",
            "alternatives": ["triumph or flatline", "execution or extinction", "all-in stakes"]
        },
        "play your cards": {
            "category": "attitude",
            "alternatives": ["manage the hand", "strategize the draw", "deploy the assets"]
        },
        "ace up my sleeve": {
            "category": "triumph",
            "alternatives": ["hidden trump card", "concealed leverage", "secret resource"]
        },
        "out of control": {
            "category": "madness",
            "alternatives": ["steering disconnected", "beyond guidance system", "unbounded chaos"]
        },
        "under pressure": {
            "category": "struggle",
            "alternatives": ["encased in tension", "bearing the weight load", "atmospheric crush"]
        },
        "against the odds": {
            "category": "struggle",
            "alternatives": ["defying probabilities", "facing skewed distributions", "refusing the baseline math"]
        },
        "prove them wrong": {
            "category": "ambition",
            "alternatives": ["refute their projections", "dethrone their assumptions", "dismantle the skepticism"]
        },
        "lose control": {
            "category": "madness",
            "alternatives": ["slip the anchor", "dethrone the steering wheel", "unbridle the energy"]
        },
        "living large": {
            "category": "lifestyle",
            "alternatives": ["dwelling in scale", "expansive habits", "oversized prints"]
        },
        "city never sleeps": {
            "category": "city",
            "alternatives": ["twenty-four hour concrete", "insomniac streets", "skyline never dims"]
        },
        "shining bright": {
            "category": "flexing",
            "alternatives": ["emitting high lumens", "dazzling visual space", "radiating glare"]
        },
        "wake up call": {
            "category": "time",
            "alternatives": ["alarm in the system", "clarifying signal", "jolt of awareness"]
        },
        "chasing paper": {
            "category": "wealth",
            "alternatives": ["hunting currency", "shadowing the check", "pursuing the banknote"]
        },
        "cash is king": {
            "category": "wealth",
            "alternatives": ["liquidity governs all", "dollar holds the scepter", "currency reigns"]
        },
        "paying dues": {
            "category": "effort",
            "alternatives": ["settling back-taxes", "covering the entrance fee", "purchasing credibility"]
        },
        "breaking the rules": {
            "category": "danger",
            "alternatives": ["shattering codices", "transgressing standard scripts", "violating parameters"]
        },
        "on the rise": {
            "category": "ambition",
            "alternatives": ["gaining altitude", "climbing coordinates", "upward draft"]
        },
        "all in": {
            "category": "attitude",
            "alternatives": ["total exposure", "one hundred percent committed", "unreserved stake"]
        },
        "double down": {
            "category": "attitude",
            "alternatives": ["multiply the wager", "re-exposing stakes", "strengthening commitments"]
        },
        "living legend": {
            "category": "triumph",
            "alternatives": ["mythology in real time", "breathing monument", "immortalized while active"]
        },
        "too hot to handle": {
            "category": "danger",
            "alternatives": ["thermal overload", "unmanageable heat", "scorching levels"]
        },
        "staying alive": {
            "category": "struggle",
            "alternatives": ["maintaining pulse rate", "clinging to timeline", "preserving biology"]
        },
        "on the edge": {
            "category": "danger",
            "alternatives": ["perched on the precipice", "borderline state", "brinkmanship"]
        },
        "skating on thin ice": {
            "category": "danger",
            "alternatives": ["gliding fragile surfaces", "testing the thickness", "risking structural failure"]
        },
        "burning bridges": {
            "category": "change",
            "alternatives": ["demolishing pathways behind", "severing exit corridors", "combusting routes"]
        },
        "turning the page": {
            "category": "change",
            "alternatives": ["flipping the chapter", "shifting the narrative", "unrolling new parchment"]
        },
        "point of no return": {
            "category": "inevitable",
            "alternatives": ["event horizon reached", "bridges fully burned", "rubicon crossed"]
        }
    }

    def detect(self, lines: List[str], avoided_words: Optional[Set[str]] = None) -> List[Dict]:
        """
        Scan lines for overused clichés and words that should be avoided.
        Returns list of detections with alternatives and categories.
        """
        detections = []
        avoided_words = avoided_words or set()

        for idx, line in enumerate(lines):
            line_clean = line.lower().strip()
            if not line_clean:
                continue

            # 1. Check direct clichés
            for cliche, details in self.CLICHE_DICT.items():
                if cliche in line_clean:
                    detections.append({
                        "line_index": idx,
                        "phrase": cliche,
                        "category": details["category"],
                        "alternatives": details["alternatives"],
                        "severity": "high",
                        "reason": "Overused hip-hop cliché"
                    })

            # 2. Check avoided words
            words = re.findall(r"[a-z']+", line_clean)
            for w in words:
                if w in avoided_words:
                    detections.append({
                        "line_index": idx,
                        "phrase": w,
                        "category": "avoided",
                        "alternatives": [],
                        "severity": "medium",
                        "reason": "Avoided word list"
                    })

        return detections

