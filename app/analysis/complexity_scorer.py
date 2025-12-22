"""
Complexity Scorer
Rates lyric complexity on multiple dimensions
"""
from typing import List, Dict
from .rhyme_detector import RhymeDetector
from .syllable_counter import SyllableCounter


class ComplexityScorer:
    """Scores lyrics on various complexity dimensions"""
    
    def __init__(self):
        self.rhyme_detector = RhymeDetector()
        self.syllable_counter = SyllableCounter()
        
        # Words indicating higher vocabulary complexity
        self.advanced_vocab_patterns = [
            # Multisyllabic words are naturally more complex
            # Will be analyzed dynamically
        ]
    
    def score_line(self, line: str, previous_lines: List[str] = None) -> Dict:
        """
        Score a single line's complexity
        Returns scores from 0.0 to 1.0 for each dimension
        """
        scores = {}
        
        # 1. Internal rhyme density (0-1)
        internal_rhymes = self.rhyme_detector.detect_internal_rhymes(line)
        words = line.split()
        word_count = len(words)
        
        if word_count > 0:
            rhyme_density = len(internal_rhymes) * 2 / word_count
            scores["internal_rhyme"] = min(1.0, rhyme_density)
        else:
            scores["internal_rhyme"] = 0.0
        
        # 2. Vocabulary complexity (avg syllables per word)
        breakdown = self.syllable_counter.get_line_breakdown(line)
        if breakdown:
            avg_syllables = sum(w["syllables"] for w in breakdown) / len(breakdown)
            # Map 1-4+ syllables to 0-1 score
            scores["vocabulary"] = min(1.0, (avg_syllables - 1) / 3)
        else:
            scores["vocabulary"] = 0.0
        
        # 3. Line length complexity (8-16 words is optimal)
        if 8 <= word_count <= 16:
            scores["density"] = 0.8 + (16 - abs(word_count - 12)) / 80
        elif word_count < 8:
            scores["density"] = word_count / 10
        else:
            scores["density"] = max(0.5, 1.0 - (word_count - 16) / 20)
        
        # 4. Rhyme scheme complexity (with previous lines)
        if previous_lines:
            all_lines = previous_lines + [line]
            rhyme_analysis = self.rhyme_detector.analyze_line(line, previous_lines)
            rhyme_connections = len(rhyme_analysis.get("rhymes_with_previous", []))
            scores["rhyme_scheme"] = min(1.0, rhyme_connections / 2 + 0.3)
        else:
            scores["rhyme_scheme"] = 0.5  # Default for first line
        
        # Overall score (weighted average)
        weights = {
            "internal_rhyme": 0.3,
            "vocabulary": 0.2,
            "density": 0.2,
            "rhyme_scheme": 0.3
        }
        
        overall = sum(scores[k] * weights[k] for k in weights)
        scores["overall"] = round(overall, 2)
        
        return scores
    
    def score_verse(self, lines: List[str]) -> Dict:
        """
        Score an entire verse
        """
        if not lines:
            return {"overall": 0.0, "lines": []}
        
        line_scores = []
        for i, line in enumerate(lines):
            previous = lines[:i] if i > 0 else None
            score = self.score_line(line, previous)
            line_scores.append(score)
        
        # Aggregate scores
        avg_scores = {}
        for key in line_scores[0].keys():
            avg_scores[key] = round(
                sum(ls[key] for ls in line_scores) / len(line_scores), 2
            )
        
        # Additional verse-level metrics
        rhyme_scheme = self.rhyme_detector.get_rhyme_scheme_string(lines)
        
        # Rhyme scheme variety (more unique letters = less repetitive)
        unique_rhymes = len(set(rhyme_scheme.replace('X', '')))
        rhyme_variety = unique_rhymes / len(lines) if lines else 0
        avg_scores["rhyme_variety"] = round(rhyme_variety, 2)
        
        # Check for multisyllabic rhymes
        multisyllabic_count = 0
        for i in range(len(lines) - 1):
            ms = self.rhyme_detector.detect_multisyllabic_rhymes(lines[i], lines[i + 1])
            multisyllabic_count += len(ms)
        
        avg_scores["multisyllabic_rhymes"] = multisyllabic_count
        
        return {
            "overall": avg_scores["overall"],
            "dimensions": avg_scores,
            "rhyme_scheme": rhyme_scheme,
            "line_count": len(lines),
            "line_scores": line_scores
        }
    
    def get_complexity_label(self, score: float) -> str:
        """Convert score to human-readable label"""
        if score < 0.3:
            return "Simple"
        elif score < 0.5:
            return "Moderate"
        elif score < 0.7:
            return "Complex"
        elif score < 0.85:
            return "Advanced"
        else:
            return "Expert"
    
    def compare_to_style(self, lines: List[str], style: str) -> Dict:
        """
        Compare verse complexity to known artist styles
        """
        # Approximate complexity targets by style
        style_targets = {
            "kendrick": {"internal_rhyme": 0.7, "vocabulary": 0.7, "overall": 0.75},
            "drake": {"internal_rhyme": 0.4, "vocabulary": 0.5, "overall": 0.5},
            "j_cole": {"internal_rhyme": 0.6, "vocabulary": 0.6, "overall": 0.65},
            "eminem": {"internal_rhyme": 0.9, "vocabulary": 0.8, "overall": 0.85},
            "travis_scott": {"internal_rhyme": 0.3, "vocabulary": 0.4, "overall": 0.4},
            "nas": {"internal_rhyme": 0.6, "vocabulary": 0.7, "overall": 0.7},
            "migos": {"internal_rhyme": 0.3, "vocabulary": 0.3, "overall": 0.35},
        }
        
        verse_score = self.score_verse(lines)
        target = style_targets.get(style.lower(), style_targets["drake"])
        
        comparison = {}
        for key in target:
            current = verse_score["dimensions"].get(key, verse_score.get(key, 0))
            comparison[key] = {
                "current": current,
                "target": target[key],
                "difference": round(current - target[key], 2)
            }
        
        return {
            "style": style,
            "your_score": verse_score,
            "comparison": comparison
        }
    
    def get_improvement_suggestions(self, score: Dict) -> List[str]:
        """
        Generate suggestions based on complexity scores
        """
        suggestions = []
        dims = score.get("dimensions", score)
        
        if dims.get("internal_rhyme", 0) < 0.4:
            suggestions.append("Try adding rhymes within your lines (internal rhymes)")
        
        if dims.get("vocabulary", 0) < 0.3:
            suggestions.append("Consider using some longer, multisyllabic words")
        
        if dims.get("rhyme_scheme", 0) < 0.4:
            suggestions.append("Create stronger connections between line endings")
        
        if dims.get("rhyme_variety", 0) and dims["rhyme_variety"] < 0.3:
            suggestions.append("Mix up your rhyme scheme - try ABAB or ABCABC patterns")
        
        if dims.get("multisyllabic_rhymes", 0) == 0:
            suggestions.append("Try multi-word rhymes for added complexity")
        
        if not suggestions:
            suggestions.append("Your complexity level is solid! Keep developing your style.")
        
        return suggestions
