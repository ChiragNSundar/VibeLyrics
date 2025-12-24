"""
Analysis package initialization
"""
from .rhyme_detector import RhymeDetector
from .syllable_counter import SyllableCounter
from .bpm_calculator import BPMCalculator
from .complexity_scorer import ComplexityScorer
from .rhyme_dictionary import RhymeDictionary, get_rhyme_dictionary
from .indian_thesaurus import IndianThesaurus, get_indian_thesaurus
from .ultra_thesaurus import UltraThesaurus, get_ultra_thesaurus

__all__ = [
    'RhymeDetector',
    'SyllableCounter',
    'BPMCalculator',
    'ComplexityScorer',
    'RhymeDictionary',
    'get_rhyme_dictionary',
    'IndianThesaurus',
    'get_indian_thesaurus',
    'UltraThesaurus',
    'get_ultra_thesaurus'
]



