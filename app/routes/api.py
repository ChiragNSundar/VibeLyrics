"""
API Routes
AJAX endpoints for AI interactions and real-time features
"""
import json
from flask import Blueprint, request, jsonify
from app.models import db, LyricSession, LyricLine, JournalEntry, Correction, UserProfile
from app.ai import get_provider, get_provider_with_fallback
from app.analysis import RhymeDetector, SyllableCounter, BPMCalculator, ComplexityScorer, RhymeDictionary
from app.learning import StyleExtractor, VocabularyManager, CorrectionTracker

api_bp = Blueprint('api', __name__)


@api_bp.route('/line/add', methods=['POST'])
def add_line():
    """Add a new line to a session"""
    data = request.json
    session_id = data.get('session_id')
    user_input = data.get('line', '').strip()
    
    if not session_id or not user_input:
        return jsonify({"error": "Missing session_id or line"}), 400
    
    session = LyricSession.query.get_or_404(session_id)
    
    # Get next line number
    last_line = session.lines.order_by(LyricLine.line_number.desc()).first()
    line_number = (last_line.line_number + 1) if last_line else 1
    
    # Analyze the line
    syllable_counter = SyllableCounter()
    rhyme_detector = RhymeDetector()
    
    syllable_count = syllable_counter.count_line_syllables(user_input)
    
    # Check for internal rhymes
    internal_rhymes = rhyme_detector.detect_internal_rhymes(user_input)
    
    # Create the line
    line = LyricLine(
        session_id=session_id,
        line_number=line_number,
        user_input=user_input,
        final_version=user_input,
        syllable_count=syllable_count,
        has_internal_rhyme=len(internal_rhymes) > 0
    )
    
    db.session.add(line)
    db.session.commit()
    
    # Track vocabulary
    vocab_manager = VocabularyManager()
    vocab_manager.track_words(user_input)
    
    return jsonify({
        "success": True,
        "line_id": line.id,
        "line_number": line_number,
        "syllable_count": syllable_count,
        "has_internal_rhyme": line.has_internal_rhyme,
        "internal_rhymes": internal_rhymes
    })


@api_bp.route('/line/suggest', methods=['POST'])
def suggest_line():
    """Get AI suggestion for next line or improvement"""
    data = request.json
    session_id = data.get('session_id')
    action = data.get('action', 'next')  # next, improve
    current_line = data.get('current_line', '')
    improvement_type = data.get('improvement_type', 'rhyme')
    
    session = LyricSession.query.get_or_404(session_id)
    profile = UserProfile.get_or_create_default()
    
    # Get previous lines for context
    lines = session.lines.all()
    previous_lines = [l.final_version or l.user_input for l in lines]
    
    # Get style context
    style_extractor = StyleExtractor()
    style_context = style_extractor.get_style_summary()
    
    # Get AI provider
    try:
        provider = get_provider(profile.preferred_provider)
    except Exception as e:
        return jsonify({"error": f"AI provider error: {str(e)}"}), 500
    
    try:
        if action == 'next':
            result = provider.suggest_next_line(
                previous_lines=previous_lines,
                bpm=session.bpm,
                style_context=style_context
            )
        elif action == 'improve':
            result = provider.improve_line(
                line=current_line,
                improvement_type=improvement_type,
                bpm=session.bpm,
                style_context=style_context
            )
        else:
            return jsonify({"error": "Invalid action"}), 400
        
        return jsonify({
            "success": True,
            "result": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/line/accept', methods=['POST'])
def accept_suggestion():
    """Accept an AI suggestion (optionally with modifications)"""
    data = request.json
    line_id = data.get('line_id')
    original_suggestion = data.get('original_suggestion', '')
    accepted_version = data.get('accepted_version', '')
    
    line = LyricLine.query.get_or_404(line_id)
    
    # Store the AI suggestion
    line.ai_suggestion = original_suggestion
    line.final_version = accepted_version
    
    # Check if user modified the suggestion
    if original_suggestion and accepted_version != original_suggestion:
        line.was_corrected = True
        
        # Track the correction for learning
        correction_tracker = CorrectionTracker()
        correction_tracker.track_correction(
            original=original_suggestion,
            corrected=accepted_version,
            line_id=line.id,
            session_id=line.session_id
        )
    
    db.session.commit()
    
    return jsonify({"success": True})


@api_bp.route('/line/analyze', methods=['POST'])
def analyze_line():
    """Analyze a single line"""
    data = request.json
    line = data.get('line', '')
    bpm = data.get('bpm', 140)
    previous_lines = data.get('previous_lines', [])
    
    syllable_counter = SyllableCounter()
    rhyme_detector = RhymeDetector()
    bpm_calculator = BPMCalculator()
    complexity_scorer = ComplexityScorer()
    
    # Syllable analysis
    syllable_info = syllable_counter.analyze_flow(line, bpm_calculator.get_syllable_target(bpm)['optimal'])
    
    # Rhyme analysis
    rhyme_info = rhyme_detector.analyze_line(line, previous_lines)
    
    # Complexity
    complexity = complexity_scorer.score_line(line, previous_lines)
    
    # BPM fit
    bpm_fit = bpm_calculator.analyze_bar_timing(line, bpm)
    
    return jsonify({
        "syllables": syllable_info,
        "rhymes": rhyme_info,
        "complexity": complexity,
        "bpm_fit": bpm_fit
    })


@api_bp.route('/session/<int:session_id>/analyze', methods=['GET'])
def analyze_session(session_id):
    """Analyze entire session"""
    session = LyricSession.query.get_or_404(session_id)
    lines = [l.final_version or l.user_input for l in session.lines.all()]
    
    if not lines:
        return jsonify({"error": "No lines in session"}), 400
    
    rhyme_detector = RhymeDetector()
    complexity_scorer = ComplexityScorer()
    bpm_calculator = BPMCalculator()
    
    # Full analysis
    rhyme_scheme = rhyme_detector.get_rhyme_scheme_string(lines)
    complexity = complexity_scorer.score_verse(lines)
    suggestions = complexity_scorer.get_improvement_suggestions(complexity)
    flow_suggestions = bpm_calculator.suggest_flow_style(session.bpm)
    
    return jsonify({
        "line_count": len(lines),
        "rhyme_scheme": rhyme_scheme,
        "complexity": complexity,
        "improvement_suggestions": suggestions,
        "flow_suggestions": flow_suggestions
    })


@api_bp.route('/ask', methods=['POST'])
def ask_question():
    """Ask the AI a question about lyrics/writing"""
    data = request.json
    question = data.get('question', '')
    session_id = data.get('session_id')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    profile = UserProfile.get_or_create_default()
    provider = get_provider(profile.preferred_provider)
    
    session_context = {}
    if session_id:
        session = LyricSession.query.get(session_id)
        if session:
            session_context = {
                "bpm": session.bpm,
                "mood": session.mood,
                "theme": session.theme,
                "line_count": session.line_count
            }
    
    try:
        answer = provider.answer_user_question(question, session_context)
        return jsonify({"success": True, "answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/provider/switch', methods=['POST'])
def switch_provider():
    """Switch AI provider"""
    data = request.json
    provider = data.get('provider', 'openai')
    
    if provider not in ['openai', 'gemini', 'perplexity']:
        return jsonify({"error": "Invalid provider"}), 400
    
    profile = UserProfile.get_or_create_default()
    profile.preferred_provider = provider
    db.session.commit()
    
    return jsonify({"success": True, "provider": provider})


@api_bp.route('/line/update', methods=['POST'])
def update_line():
    """Update an existing line"""
    data = request.json
    line_id = data.get('line_id')
    new_text = data.get('text', '').strip()
    
    if not line_id or not new_text:
        return jsonify({"error": "Missing line_id or text"}), 400
    
    line = LyricLine.query.get_or_404(line_id)
    
    # Update the line
    line.user_input = new_text
    line.final_version = new_text
    
    # Re-analyze syllables
    syllable_counter = SyllableCounter()
    rhyme_detector = RhymeDetector()
    
    line.syllable_count = syllable_counter.count_line_syllables(new_text)
    internal_rhymes = rhyme_detector.detect_internal_rhymes(new_text)
    line.has_internal_rhyme = len(internal_rhymes) > 0
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "syllable_count": line.syllable_count,
        "has_internal_rhyme": line.has_internal_rhyme
    })


@api_bp.route('/line/delete', methods=['POST'])
def delete_line():
    """Delete a line"""
    data = request.json
    line_id = data.get('line_id')
    
    if not line_id:
        return jsonify({"error": "Missing line_id"}), 400
    
    line = LyricLine.query.get_or_404(line_id)
    session_id = line.session_id
    
    db.session.delete(line)
    db.session.commit()
    
    # Renumber remaining lines
    session = LyricSession.query.get(session_id)
    for i, l in enumerate(session.lines.order_by(LyricLine.id).all(), 1):
        l.line_number = i
    db.session.commit()
    
    return jsonify({"success": True})


@api_bp.route('/rhyme/lookup', methods=['POST'])
def lookup_rhyme():
    """Look up rhymes for a word"""
    data = request.json
    word = data.get('word', '').strip()
    
    if not word:
        return jsonify({"error": "Word required"}), 400
    
    dictionary = RhymeDictionary()
    info = dictionary.get_rhyme_info(word)
    
    return jsonify({
        "success": True,
        "word": word,
        "rhymes": info['exact_rhymes'],
        "syllables": info['syllables'],
        "multisyllabic": info['multisyllabic']
    })


@api_bp.route('/rhyme/slang/<category>', methods=['GET'])
def get_slang(category):
    """Get hip-hop slang for a category"""
    dictionary = RhymeDictionary()
    synonyms = dictionary.get_synonyms(category)
    
    if not synonyms:
        return jsonify({
            "success": True,
            "category": category,
            "synonyms": [],
            "available_categories": dictionary.get_all_categories()
        })
    
    return jsonify({
        "success": True,
        "category": category,
        "synonyms": synonyms
    })


@api_bp.route('/rhyme/categories', methods=['GET'])
def get_categories():
    """Get all available slang categories"""
    dictionary = RhymeDictionary()
    return jsonify({
        "success": True,
        "categories": dictionary.get_all_categories()
    })


@api_bp.route('/tools/lookup', methods=['GET'])
def lookup_tool():
    """Combined lookup for rhymes and synonyms"""
    word = request.args.get('word', '').lower().strip()
    lookup_type = request.args.get('type', 'rhyme')  # rhyme or synonym
    
    if not word:
        return jsonify({"error": "No word provided"}), 400
        
    results = []
    
    if lookup_type == 'rhyme':
        # Use existing RhymeDictionary
        try:
            dictionary = RhymeDictionary()
            info = dictionary.get_rhyme_info(word)
            perfect_rhymes = info.get('exact_rhymes', [])
            
            topic = request.args.get('topic', '').strip()
            topic_rhymes = []
            
            if topic and perfect_rhymes:
                try:
                    from nltk.corpus import wordnet
                    topic_syns = wordnet.synsets(topic)
                    
                    scored_rhymes = []
                    for r_word in perfect_rhymes:
                        r_syns = wordnet.synsets(r_word)
                        if not r_syns: continue
                        
                        max_score = 0
                        for t_syn in topic_syns:
                            for r_syn in r_syns:
                                # wup_similarity is often better for semantic relatedness than path_similarity
                                score = t_syn.wup_similarity(r_syn)
                                if score and score > max_score:
                                    max_score = score
                        
                        if max_score > 0.3: # Threshold
                            scored_rhymes.append((r_word, max_score))
                    
                    # Sort by score desc
                    scored_rhymes.sort(key=lambda x: x[1], reverse=True)
                    topic_rhymes = [x[0] for x in scored_rhymes]
                except ImportError:
                    pass # NLTK not ready or error
            
            results = {
                "perfect": perfect_rhymes[:30], # Standard rhymes
                "pocket": dictionary.find_pocket_rhymes(word, max_results=15), # Rhymes that match flow
                "topic_rhymes": topic_rhymes[:15], # Contextual rhymes
                "slant": []
            }
        except Exception as e:
            results = {"perfect": [], "error": str(e)}

    elif lookup_type == 'synonym':
        try:
            from nltk.corpus import wordnet
            synonyms = set()
            antonyms = set()
            
            for syn in wordnet.synsets(word):
                for lemma in syn.lemmas():
                    name = lemma.name().replace('_', ' ')
                    if name.lower() != word:
                        synonyms.add(name)
                        if lemma.antonyms():
                            for ant in lemma.antonyms():
                                antonyms.add(ant.name().replace('_', ' '))
            
            # Enrich with syllable counts
            syllable_counter = SyllableCounter()
            
            def enrich(word_list):
                enriched = []
                for w in word_list:
                    enriched.append({
                        'word': w,
                        'syllables': syllable_counter.count_syllables_phrase(w) if ' ' in w else syllable_counter.count_syllables(w)
                    })
                # Sort by syllable count then length
                return sorted(enriched, key=lambda x: (x['syllables'], len(x['word'])))

            results = {
                'synonyms': enrich(list(synonyms)[:30]), # Limit results
                'antonyms': enrich(list(antonyms)[:15])
            }
            
        except Exception as e:
            results = {"error": f"Error loading data: {e}"}
            print(f"Synonym error: {e}")
            
    return jsonify({
        "success": True,
        "word": word,
        "type": lookup_type,
        "results": results
    })
            
    return jsonify({
        "success": True,
        "word": word,
        "type": lookup_type,
        "results": results
    })


@api_bp.route('/analysis/dna', methods=['POST'])
def analyze_dna():
    """Analyze Artist DNA based on writing style"""
    # This is a mock implementation. In a real scenario, we'd feed 
    # all user content to the LLM to classify style.
    
    # Calculate some basic stats to influence the result
    profile = UserProfile.get_or_create_default()
    sessions = LyricSession.query.all()
    avg_bpm = sum([s.bpm for s in sessions]) / max(len(sessions), 1)
    
    # Mock logic
    dna_profile = []
    
    if avg_bpm < 90:
        dna_profile = [
            {"artist": "Nas", "score": 35, "trait": "Introspective & Lyrical"},
            {"artist": "J. Cole", "score": 25, "trait": "Storytelling"},
            {"artist": "Kendrick Lamar", "score": 20, "trait": "Complex Flows"}
        ]
    elif avg_bpm > 140:
        dna_profile = [
            {"artist": "Travis Scott", "score": 40, "trait": "Hype & Energy"},
            {"artist": "Playboi Carti", "score": 30, "trait": "Experimental"},
            {"artist": "Drake", "score": 20, "trait": "Hit Maker"}
        ]
    else:
        dna_profile = [
            {"artist": "Drake", "score": 35, "trait": "Versatile"},
            {"artist": "Kanye West", "score": 30, "trait": "Creative"},
            {"artist": "Jay-Z", "score": 20, "trait": "Business Flow"}
        ]
        
    return jsonify({
        "success": True,
        "dna": dna_profile,
        "summary": "Your style leans towards " + dna_profile[0]['trait']
    })

