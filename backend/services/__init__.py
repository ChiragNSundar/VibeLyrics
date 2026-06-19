"""
Services package
"""
from .rhyme_detector import RhymeDetector, SyllableCounter
from .ai_provider import get_ai_provider, set_provider
from .advanced_analysis import PunchlineEngine, MetaphorGenerator, ComplexityScorer, ImageryAnalyzer
from .learning import StyleExtractor, VocabularyManager, CorrectionTracker, ClicheDetector
from .references import FolderManager, TxtParser, StructuredParser
from .audio import AudioAnalyzer, AdlibGenerator
from .nlp_analysis import WordplayEngine, RhymeComplexityScorer, SemanticDriftDetector, ThemeClusterer
from .training_data import TrainingDataGenerator, SuggestionTracker, LMStudioTrainingManager, MicroFeedbackTracker, LoRAProfileManager, RLHFTracker, ContinualLearningManager, ConceptEraser
from .syllable_utils import count_syllables, count_syllables_text
from .cache import PersistentCache, persistent_cached

