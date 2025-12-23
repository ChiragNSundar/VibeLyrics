"""
References Routes
Reference lyrics management
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.references import FolderManager, TxtParser, StructuredParser, GeniusScraper
from app.analysis import RhymeDetector, ComplexityScorer

references_bp = Blueprint('references', __name__)


@references_bp.route('/')
def index():
    """References library page"""
    folder_manager = FolderManager()
    files = folder_manager.list_all_files()
    stats = folder_manager.get_statistics()
    
    # Check if Genius is configured
    genius = GeniusScraper()
    genius_configured = genius.is_configured()
    
    return render_template('references.html',
                         files=files,
                         stats=stats,
                         genius_configured=genius_configured)


@references_bp.route('/view/<path:filename>')
def view_file(filename):
    """View a reference lyrics file"""
    folder_manager = FolderManager()
    content = folder_manager.get_file_content(filename)
    
    if content is None:
        return "File not found", 404
    
    # Parse the content
    structured_parser = StructuredParser()
    txt_parser = TxtParser()
    
    if structured_parser.is_structured(content):
        parsed = structured_parser.parse(content)
    else:
        parsed = {"lyrics": txt_parser.parse(content), "metadata": {}}
    
    # Analyze the lyrics
    lines = parsed["lyrics"].get("all_lines", [])
    
    analysis = {}
    if lines:
        rhyme_detector = RhymeDetector()
        complexity_scorer = ComplexityScorer()
        
        analysis = {
            "rhyme_scheme": rhyme_detector.get_rhyme_scheme_string(lines[:16]),
            "complexity": complexity_scorer.score_verse(lines[:16]),
            "structure": txt_parser.analyze_structure(content)
        }
        
        # Enrich sections with visual highlights
        if "sections" in parsed["lyrics"]:
            for section in parsed["lyrics"]["sections"]:
                section_lines = section["lines"]
                if section_lines:
                    section["lines"] = rhyme_detector.highlight_lyrics(section_lines)
        
        # --- AUTO-LEARN FROM REFERENCE ---
        # Silently learn patterns from viewed reference to improve suggestions
        try:
            from app.learning import StyleExtractor
            style_extractor = StyleExtractor()
            
            # Extract patterns (only first 32 lines to avoid skewing with long songs)
            ref_analysis = style_extractor.analyze_lines(lines[:32])
            
            # Update vocabulary with new words (but don't overwrite favorites)
            if ref_analysis.get("common_words"):
                vocab = style_extractor.style_data.get("vocabulary", {})
                current_words = set(vocab.get("learned_from_refs", []))
                current_words.update(ref_analysis["common_words"][:5])
                vocab["learned_from_refs"] = list(current_words)[:100]  # Cap at 100
                style_extractor.save_style()
        except Exception:
            pass  # Silently fail - learning is non-critical
    
    return render_template('reference_view.html',
                         filename=filename,
                         content=content,
                         parsed=parsed,
                         analysis=analysis)


@references_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload a new lyrics file"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith(('.txt', '.md', '.lyrics')):
        return jsonify({"error": "Invalid file type"}), 400
    
    content = file.read().decode('utf-8')
    
    # Try to extract artist/song from filename
    filename = file.filename.rsplit('.', 1)[0]
    if ' - ' in filename:
        artist, song = filename.split(' - ', 1)
    else:
        artist = "Unknown"
        song = filename
    
    folder_manager = FolderManager()
    filepath = folder_manager.add_lyrics_file(
        content=content,
        artist=artist,
        song_title=song,
        structured=True
    )
    
    return jsonify({"success": True, "path": filepath})


@references_bp.route('/add-manual', methods=['POST'])
def add_manual():
    """Manually add lyrics"""
    artist = request.form.get('artist', 'Unknown')
    song = request.form.get('song', 'Untitled')
    lyrics = request.form.get('lyrics', '')
    
    if not lyrics:
        return jsonify({"error": "Lyrics required"}), 400
    
    folder_manager = FolderManager()
    filepath = folder_manager.add_lyrics_file(
        content=lyrics,
        artist=artist,
        song_title=song,
        structured=True
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": True, "path": filepath})
    
    return redirect(url_for('references.index'))


@references_bp.route('/search')
def search():
    """Search reference lyrics"""
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('references.index'))
    
    folder_manager = FolderManager()
    results = folder_manager.search_files(query)
    
    return render_template('references.html',
                         files=results,
                         search_query=query,
                         stats=folder_manager.get_statistics(),
                         genius_configured=GeniusScraper().is_configured())


@references_bp.route('/genius/search', methods=['POST'])
def genius_search():
    """Search Genius for lyrics"""
    query = request.json.get('query', '')
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    genius = GeniusScraper()
    
    if not genius.is_configured():
        return jsonify({"error": "Genius API not configured"}), 400
    
    try:
        results = genius.search(query, limit=10)
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@references_bp.route('/genius/fetch', methods=['POST'])
def genius_fetch():
    """Fetch and save lyrics from Genius"""
    data = request.json
    song_url = data.get('url', '')
    artist = data.get('artist', 'Unknown')
    title = data.get('title', 'Untitled')
    
    if not song_url:
        return jsonify({"error": "Song URL required"}), 400
    
    genius = GeniusScraper()
    
    if not genius.is_configured():
        return jsonify({"error": "Genius API not configured"}), 400
    
    try:
        lyrics = genius.get_lyrics(song_url)
        
        if not lyrics:
            return jsonify({"error": "Could not fetch lyrics"}), 500
        
        folder_manager = FolderManager()
        filepath = folder_manager.add_lyrics_file(
            content=lyrics,
            artist=artist,
            song_title=title,
            structured=True
        )
        
        return jsonify({
            "success": True,
            "path": filepath,
            "preview": lyrics[:500]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@references_bp.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    """Delete a reference file"""
    folder_manager = FolderManager()
    success = folder_manager.delete_file(filename)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": success})
    
    return redirect(url_for('references.index'))
