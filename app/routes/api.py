"""
API Routes
AJAX endpoints for AI interactions and real-time features
"""
import json
from flask import Blueprint, request, jsonify
from app.models import db, LyricSession, LyricLine, JournalEntry, Correction, UserProfile
from app.ai import get_provider, get_provider_with_fallback
from app.analysis import RhymeDetector, SyllableCounter, BPMCalculator, ComplexityScorer, RhymeDictionary, get_rhyme_dictionary
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
    
    # --- RAG: Index line for infinite memory ---
    try:
        from app.learning import get_vector_store
        vector_store = get_vector_store()
        vector_store.index_line(
            text=user_input,
            session_id=session_id,
            session_title=session.title
        )
    except Exception:
        pass  # RAG indexing is non-critical
    
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
    """Get AI suggestion for next line or improvement with full context awareness"""
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
    
    # Get style context (base)
    style_extractor = StyleExtractor()
    style_context = style_extractor.get_style_summary()
    
    # ========================================
    # ENHANCED CONTEXT AWARENESS
    # ========================================
    
    # 1. Detect current rhyme scheme
    try:
        from app.analysis import RhymeDetector
        rhyme_detector = RhymeDetector()
        if previous_lines:
            rhyme_scheme = rhyme_detector.get_rhyme_scheme_string(previous_lines[-8:])  # Last 8 lines
            style_context["current_rhyme_scheme"] = rhyme_scheme
            style_context["rhyme_hint"] = f"Current pattern is {rhyme_scheme}. Continue or create contrast."
    except Exception:
        pass
    
    # 2. Extract themes from recent lines
    try:
        recent_text = " ".join(previous_lines[-4:]) if previous_lines else ""
        if recent_text:
            # Simple keyword extraction
            words = recent_text.lower().split()
            theme_words = [w for w in set(words) if len(w) > 4 and w.isalpha()][:5]
            style_context["recent_themes"] = theme_words
            style_context["theme_hint"] = f"Recent themes/words: {', '.join(theme_words)}"
    except Exception:
        pass
    
    # 3. Get syllable pattern for flow matching
    if lines:
        recent_syllables = [l.syllable_count for l in lines[-4:] if l.syllable_count]
        if recent_syllables:
            avg_syl = sum(recent_syllables) / len(recent_syllables)
            style_context["target_syllables"] = round(avg_syl)
            style_context["syllable_hint"] = f"Match ~{round(avg_syl)} syllables for consistent flow."
    
    # 4. RAG: Retrieve similar past lyrics
    rag_context = ""
    try:
        from app.learning import get_vector_store
        vector_store = get_vector_store()
        
        query_text = " ".join(previous_lines[-2:]) if previous_lines else ""
        if query_text:
            similar_lines = vector_store.search_similar(
                query=query_text,
                top_k=3,
                exclude_session_id=session_id
            )
            rag_context = vector_store.format_for_prompt(similar_lines)
    except Exception:
        pass
    
    if rag_context:
        style_context["rag_memory"] = rag_context
        style_context["memory_hint"] = "Reference your past style from these similar lines."
    
    # 5. Get learned corrections/preferences
    try:
        learned_prefs = profile.style_profile_data or {}
        if "consolidated_insights" in learned_prefs:
            insights = learned_prefs["consolidated_insights"]
            if insights.get("preferences"):
                style_context["learned_preferences"] = insights["preferences"]
            if insights.get("avoided_words"):
                style_context["avoid_words"] = insights["avoided_words"]
    except Exception:
        pass
    
    # 6. Build elite context if not improving
    try:
        from app.ai.context_builder import ContextBuilder
        context_builder = ContextBuilder()
        style_context["elite_prompt"] = context_builder.build_elite_prompt(session, profile)
    except Exception:
        pass
    
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
        
        # Include context hints in response for transparency
        return jsonify({
            "success": True,
            "result": result,
            "context_used": {
                "previous_lines": len(previous_lines),
                "rhyme_scheme": style_context.get("current_rhyme_scheme", ""),
                "target_syllables": style_context.get("target_syllables", 12),
                "has_rag_memory": bool(rag_context)
            }
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
    else:
        # User accepted suggestion as-is - learn from it!
        try:
            from app.learning import StyleExtractor
            style_extractor = StyleExtractor()
            
            # Extract key words from accepted suggestion
            words = [w.strip('.,!?;:"\'').lower() for w in accepted_version.split() 
                    if len(w) > 3]
            
            # Update vocabulary with accepted words
            vocab = style_extractor.style_data.get("vocabulary", {})
            favorites = set(vocab.get("favorite_words", []))
            favorites.update(words[-3:])  # Add last 3 words (often rhyme words)
            vocab["favorite_words"] = list(favorites)[:50]
            
            # Track acceptance rate
            patterns = style_extractor.style_data.get("learned_patterns", {})
            patterns["suggestions_accepted"] = patterns.get("suggestions_accepted", 0) + 1
            
            style_extractor.save_style()
        except Exception:
            pass  # Learning is non-critical
    
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
    
    dictionary = get_rhyme_dictionary()
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
    dictionary = get_rhyme_dictionary()
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
    dictionary = get_rhyme_dictionary()
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
            dictionary = get_rhyme_dictionary()
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


@api_bp.route('/challenge/today', methods=['GET'])
def get_daily_challenge():
    """Get today's daily challenge word"""
    import hashlib
    from datetime import date
    
    # Word bank for challenges - hip-hop focused vocabulary
    challenge_words = [
        ("Cipher", "Drop a bar about circles or cycles"),
        ("Crown", "Write about royalty or achievement"),
        ("Hustle", "Capture the grind mentality"),
        ("Legacy", "What will you leave behind?"),
        ("Mirror", "Reflect on yourself or your reflection"),
        ("Shadow", "Write about darkness or following"),
        ("Fire", "Bring the heat with this one"),
        ("Chain", "Links, jewelry, or being tied down"),
        ("Streets", "The concrete jungle"),
        ("Dreams", "Aspirations and nightmares"),
        ("Time", "The ultimate boss"),
        ("Pain", "Turn struggle into art"),
        ("Gold", "Wealth, value, or the color"),
        ("Soul", "The essence within"),
        ("Rise", "Coming up from the bottom"),
        ("Storm", "Weather the chaos"),
        ("Blood", "Family, sacrifice, or life"),
        ("Ghost", "The past that haunts"),
        ("Light", "Hope in darkness"),
        ("War", "Internal or external battles"),
        ("King", "Claim your throne"),
        ("Mask", "What you show vs what you hide"),
        ("Game", "Play it or get played"),
        ("Wave", "Ride it or create your own"),
        ("Snake", "Trust issues and betrayal"),
        ("Money", "The root and the fruit"),
        ("Power", "Take it or give it away"),
        ("Heart", "The core of everything"),
    ]
    
    # Use date as seed for consistent daily selection
    today = date.today().isoformat()
    seed = int(hashlib.md5(today.encode()).hexdigest(), 16)
    index = seed % len(challenge_words)
    
    word, prompt = challenge_words[index]
    
    return jsonify({
        "success": True,
        "word": word,
        "prompt": prompt,
        "date": today
    })


@api_bp.route('/user/vocabulary', methods=['GET'])
def get_user_vocabulary():
    """Get user's learned vocabulary for smarter suggestions"""
    try:
        from app.learning import StyleExtractor
        style_extractor = StyleExtractor()
        
        vocab = style_extractor.style_data.get("vocabulary", {})
        patterns = style_extractor.style_data.get("learned_patterns", {})
        
        return jsonify({
            "success": True,
            "favorite_words": vocab.get("favorite_words", [])[:30],
            "favorite_slangs": vocab.get("favorite_slangs", [])[:10],
            "learned_from_refs": vocab.get("learned_from_refs", [])[:20],
            "avoided_words": vocab.get("avoided_words", []),
            "avg_syllables": patterns.get("avg_syllables_per_line", 12),
            "suggestions_accepted": patterns.get("suggestions_accepted", 0)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/audio/energy', methods=['GET'])
def get_audio_energy():
    """Get energy sections for a session's audio track"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    
    session = LyricSession.query.get_or_404(session_id)
    
    if not session.audio_path:
        return jsonify({"success": True, "sections": []})
    
    try:
        from app.analysis.audio_analyzer import analyze_energy_sections
        import os
        
        audio_file = os.path.join('app', 'static', session.audio_path)
        sections = analyze_energy_sections(audio_file)
        
        return jsonify({
            "success": True,
            "sections": sections
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/memory/stats', methods=['GET'])
def get_memory_stats():
    """Get RAG memory statistics"""
    try:
        from app.learning import get_vector_store
        vector_store = get_vector_store()
        stats = vector_store.get_stats()
        
        return jsonify({
            "success": True,
            "total_lines_memorized": stats.get("total_lines", 0),
            "unique_sessions": stats.get("unique_sessions", 0)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/rhyme/concept/<word>', methods=['GET'])
def get_concept_rhymes(word):
    """Get semantic concept rhymes - words that rhyme AND relate by meaning"""
    try:
        from app.analysis.concept_rhymes import get_concept_rhymes as find_concept_rhymes
        
        result = find_concept_rhymes(word)
        
        return jsonify({
            "success": True,
            "word": word,
            "concept_rhymes": result["concept_rhymes"],
            "related_words": result["related_only"][:10],
            "standard_rhymes": result["rhymes_only"][:10],
            "hip_hop_related": result["hip_hop_related"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/rhyme/mindmap', methods=['POST'])
def build_verse_mindmap():
    """Build a semantic mind map from verse lines"""
    try:
        from app.analysis.concept_rhymes import build_mind_map
        
        data = request.json
        lines = data.get('lines', [])
        
        if not lines:
            return jsonify({"success": False, "error": "No lines provided"}), 400
        
        result = build_mind_map(lines)
        
        return jsonify({
            "success": True,
            "core_concepts": result["core_concepts"],
            "expanded_concepts": result["expanded_concepts"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/adlib/generate', methods=['POST'])
def generate_adlibs_endpoint():
    """Generate adlib suggestions for lyrics"""
    try:
        from app.analysis.adlib_generator import generate_adlibs_for_verse
        
        data = request.json
        lines = data.get('lines', [])
        intensity = data.get('intensity', 'medium')  # low, medium, high
        
        if not lines:
            return jsonify({"success": False, "error": "No lines provided"}), 400
        
        result = generate_adlibs_for_verse(lines, intensity)
        
        return jsonify({
            "success": True,
            "lines_with_adlibs": result["lines_with_adlibs"],
            "adlib_suggestions": result["adlib_suggestions"],
            "overall_mood": result["overall_mood"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/adlib/suggest', methods=['GET'])
def suggest_adlib():
    """Get a contextual adlib based on current context"""
    try:
        from app.analysis.adlib_generator import get_adlib_for_context
        
        context = request.args.get('context', '')
        
        adlib = get_adlib_for_context(context)
        
        return jsonify({
            "success": True,
            "adlib": adlib,
            "context": context
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============ ELITE WRITER FEATURES ============

@api_bp.route('/punchline/score', methods=['POST'])
def score_punchline():
    """Score a line's punch line potential"""
    try:
        from app.analysis.punchline_engine import score_punchline as score_punch
        
        data = request.json
        line = data.get('line', '')
        
        if not line:
            return jsonify({"success": False, "error": "No line provided"}), 400
        
        result = score_punch(line)
        
        return jsonify({
            "success": True,
            "line": line,
            "score": result["score"],
            "rating": result["rating"],
            "breakdown": result["breakdown"],
            "double_meanings": result["double_meanings"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/punchline/generate', methods=['POST'])
def generate_punchlines():
    """Generate punch line starters for a theme"""
    try:
        from app.analysis.punchline_engine import generate_punchline_starters
        
        data = request.json
        theme = data.get('theme', '')
        rhyme_word = data.get('rhyme_word')
        
        if not theme:
            return jsonify({"success": False, "error": "No theme provided"}), 400
        
        starters = generate_punchline_starters(theme, rhyme_word)
        
        return jsonify({
            "success": True,
            "theme": theme,
            "starters": starters
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/punchline/analyze', methods=['POST'])
def analyze_verse_punchlines():
    """Analyze entire verse for punch lines"""
    try:
        from app.analysis.punchline_engine import analyze_verse_for_punchlines
        
        data = request.json
        lines = data.get('lines', [])
        
        if not lines:
            return jsonify({"success": False, "error": "No lines provided"}), 400
        
        result = analyze_verse_for_punchlines(lines)
        
        return jsonify({
            "success": True,
            **result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/rhyme/multi/<word>', methods=['GET'])
def get_multi_rhymes(word):
    """Get multi-syllable rhymes"""
    try:
        from app.analysis.multi_rhyme import suggest_multi_rhyme
        
        result = suggest_multi_rhyme(word)
        
        return jsonify({
            "success": True,
            "word": word,
            "rhyme_family": result["rhyme_family"],
            "2_syllable": result["2_syllable_matches"],
            "3_syllable": result["3_syllable_matches"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/metaphor/generate', methods=['POST'])
def generate_metaphors_endpoint():
    """Generate metaphors for a concept"""
    try:
        from app.analysis.metaphor_engine import generate_metaphors
        
        data = request.json
        concept = data.get('concept', '')
        
        if not concept:
            return jsonify({"success": False, "error": "No concept provided"}), 400
        
        metaphors = generate_metaphors(concept)
        
        return jsonify({
            "success": True,
            "concept": concept,
            "metaphors": metaphors
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/simile/generate', methods=['POST'])
def generate_similes_endpoint():
    """Generate similes for a word"""
    try:
        from app.analysis.metaphor_engine import generate_similes
        
        data = request.json
        word = data.get('word', '')
        
        if not word:
            return jsonify({"success": False, "error": "No word provided"}), 400
        
        similes = generate_similes(word)
        
        return jsonify({
            "success": True,
            "word": word,
            "similes": similes
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/simile/complete', methods=['GET'])
def complete_simile_endpoint():
    """Complete a simile starter"""
    try:
        from app.analysis.metaphor_engine import complete_simile
        
        starter = request.args.get('starter', '')
        
        if not starter:
            return jsonify({"success": False, "error": "No starter provided"}), 400
        
        completions = complete_simile(starter)
        
        return jsonify({
            "success": True,
            "starter": starter,
            "completions": completions
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/imagery/analyze', methods=['POST'])
def analyze_imagery():
    """Analyze imagery density in verse"""
    try:
        from app.analysis.metaphor_engine import analyze_metaphor_density
        
        data = request.json
        lines = data.get('lines', [])
        
        if not lines:
            return jsonify({"success": False, "error": "No lines provided"}), 400
        
        result = analyze_metaphor_density(lines)
        
        return jsonify({
            "success": True,
            **result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# ADAPTIVE LEARNING ENDPOINTS
# =============================================================================

@api_bp.route('/suggestion/rate', methods=['POST'])
def rate_suggestion():
    """
    Rate an AI suggestion (thumbs up/down) to train the model on preferences.
    """
    try:
        data = request.json
        suggestion_text = data.get('suggestion', '')
        rating = data.get('rating', 0)  # 1 = good, -1 = bad
        reason = data.get('reason', '')  # e.g., "too_simple", "off_topic", "wrong_rhyme"
        
        if not suggestion_text or rating == 0:
            return jsonify({"success": False, "error": "Missing suggestion or rating"}), 400
        
        profile = UserProfile.get_or_create_default()
        style_data = profile.style_profile_data or {}
        
        # Initialize feedback history
        if "feedback_history" not in style_data:
            style_data["feedback_history"] = []
        
        # Store feedback
        from datetime import datetime
        style_data["feedback_history"].append({
            "suggestion": suggestion_text[:200],  # Truncate for storage
            "rating": rating,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep last 100 feedback items
        style_data["feedback_history"] = style_data["feedback_history"][-100:]
        
        # Update avoided patterns based on negative feedback
        if rating == -1 and reason:
            if "negative_patterns" not in style_data:
                style_data["negative_patterns"] = []
            style_data["negative_patterns"].append(reason)
            style_data["negative_patterns"] = list(set(style_data["negative_patterns"]))[-20:]
        
        profile.style_profile_data = style_data
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Feedback recorded. AI will adapt."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/correction/track', methods=['POST'])
def track_correction():
    """
    Track when user corrects an AI suggestion.
    The difference between suggestion and final version teaches the model.
    """
    try:
        from app.learning import get_correction_analyzer
        
        data = request.json
        ai_suggestion = data.get('ai_suggestion', '')
        final_version = data.get('final_version', '')
        line_id = data.get('line_id')
        
        if not ai_suggestion or not final_version:
            return jsonify({"success": False, "error": "Need both suggestion and final version"}), 400
        
        # Skip if no real correction was made
        if ai_suggestion.strip().lower() == final_version.strip().lower():
            return jsonify({"success": True, "message": "No correction detected"})
        
        # Analyze the correction
        analyzer = get_correction_analyzer()
        analysis = analyzer.analyze_correction(ai_suggestion, final_version)
        
        # Store in user profile
        profile = UserProfile.get_or_create_default()
        style_data = profile.style_profile_data or {}
        
        if "correction_history" not in style_data:
            style_data["correction_history"] = []
        
        style_data["correction_history"].append(analysis)
        
        # Keep last 50 corrections
        style_data["correction_history"] = style_data["correction_history"][-50:]
        
        profile.style_profile_data = style_data
        db.session.commit()
        
        return jsonify({
            "success": True,
            "analysis": analysis,
            "message": "Correction learned. AI will adapt."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/learning/status', methods=['GET'])
def get_learning_status():
    """
    Get the current learning status - what the AI has learned from the user.
    """
    try:
        from app.learning import get_correction_analyzer
        
        profile = UserProfile.get_or_create_default()
        style_data = profile.style_profile_data or {}
        
        corrections = style_data.get("correction_history", [])
        feedback = style_data.get("feedback_history", [])
        
        # Aggregate learnings
        analyzer = get_correction_analyzer()
        aggregated = analyzer.aggregate_learnings(corrections) if corrections else {}
        
        # Count feedback
        positive_count = len([f for f in feedback if f.get("rating") == 1])
        negative_count = len([f for f in feedback if f.get("rating") == -1])
        
        return jsonify({
            "success": True,
            "learning_stats": {
                "corrections_analyzed": len(corrections),
                "positive_feedback": positive_count,
                "negative_feedback": negative_count,
                "learned_preferences": aggregated.get("preferences", []),
                "avoided_words": aggregated.get("avoided_words", []),
                "preferred_words": aggregated.get("preferred_words", []),
                "negative_patterns": style_data.get("negative_patterns", [])
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

