"""
Settings Routes
User preferences and configuration
"""
import json
from flask import Blueprint, render_template, request, jsonify
from app.models import db, UserProfile
from app.learning import StyleExtractor, VocabularyManager, CorrectionTracker
from app.config import Config

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/')
def index():
    """Settings page"""
    profile = UserProfile.get_or_create_default()
    style_extractor = StyleExtractor()
    vocab_manager = VocabularyManager()
    correction_tracker = CorrectionTracker()
    
    # Get learned data
    style_summary = style_extractor.get_style_summary()
    vocab_context = vocab_manager.get_vocabulary_context()
    correction_insights = correction_tracker.get_correction_insights()
    
    return render_template('settings.html',
                         profile=profile,
                         style=style_summary,
                         vocab=vocab_context,
                         corrections=correction_insights,
                         config={
                             "openai_configured": bool(Config.OPENAI_API_KEY),
                             "gemini_configured": bool(Config.GEMINI_API_KEY),
                             "genius_configured": bool(Config.GENIUS_ACCESS_TOKEN)
                         })


@settings_bp.route('/update', methods=['POST'])
def update_settings():
    """Update user settings"""
    profile = UserProfile.get_or_create_default()
    
    # Update profile
    if 'preferred_provider' in request.form:
        profile.preferred_provider = request.form.get('preferred_provider')
    
    if 'default_bpm' in request.form:
        profile.default_bpm = request.form.get('default_bpm', 140, type=int)
    
    if 'complexity_level' in request.form:
        profile.complexity_level = request.form.get('complexity_level')
    
    if 'rhyme_style' in request.form:
        profile.rhyme_style = request.form.get('rhyme_style')
    
    db.session.commit()
    
    # Update style extractor settings
    style_extractor = StyleExtractor()
    
    if 'preferred_provider' in request.form:
        style_extractor.update_preference('preferred_provider', request.form.get('preferred_provider'))
    
    if 'default_bpm' in request.form:
        style_extractor.update_preference('default_bpm', int(request.form.get('default_bpm', 140)))
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": True})
    
    # Get all required context for template
    style_extractor = StyleExtractor()
    vocab_manager = VocabularyManager()
    correction_tracker = CorrectionTracker()
    
    return render_template('settings.html', 
                         profile=profile,
                         style=style_extractor.get_style_summary(),
                         vocab=vocab_manager.get_vocabulary_context(),
                         corrections=correction_tracker.get_correction_insights(),
                         config={
                             "openai_configured": bool(Config.OPENAI_API_KEY),
                             "gemini_configured": bool(Config.GEMINI_API_KEY),
                             "genius_configured": bool(Config.GENIUS_ACCESS_TOKEN)
                         },
                         message="Settings saved!")


@settings_bp.route('/vocabulary/add', methods=['POST'])
def add_vocabulary():
    """Add a word to favorites or avoided list"""
    data = request.json
    word = data.get('word', '').strip()
    list_type = data.get('type', 'favorite')  # favorite, slang, avoided
    
    if not word:
        return jsonify({"error": "Word required"}), 400
    
    vocab_manager = VocabularyManager()
    
    if list_type == 'favorite':
        vocab_manager.add_favorite(word, is_slang=False)
    elif list_type == 'slang':
        vocab_manager.add_favorite(word, is_slang=True)
    elif list_type == 'avoided':
        vocab_manager.add_avoided(word)
    
    return jsonify({"success": True})


@settings_bp.route('/vocabulary/remove', methods=['POST'])
def remove_vocabulary():
    """Remove a word from lists"""
    data = request.json
    word = data.get('word', '').strip()
    list_type = data.get('type', 'favorite')
    
    if not word:
        return jsonify({"error": "Word required"}), 400
    
    vocab_manager = VocabularyManager()
    
    if list_type in ['favorite', 'slang']:
        vocab_manager.remove_favorite(word)
    elif list_type == 'avoided':
        vocab_manager.remove_avoided(word)
    
    return jsonify({"success": True})


@settings_bp.route('/theme/add', methods=['POST'])
def add_theme():
    """Add a preferred theme"""
    data = request.json
    theme = data.get('theme', '').strip()
    
    if not theme:
        return jsonify({"error": "Theme required"}), 400
    
    style_extractor = StyleExtractor()
    style_extractor.add_preferred_theme(theme)
    
    return jsonify({"success": True})


@settings_bp.route('/stats')
def get_stats():
    """Get learning statistics"""
    profile = UserProfile.get_or_create_default()
    style_extractor = StyleExtractor()
    correction_tracker = CorrectionTracker()
    
    return jsonify({
        "profile": {
            "total_sessions": profile.total_sessions,
            "total_lines": profile.total_lines_written,
            "total_corrections": profile.total_corrections
        },
        "style": style_extractor.get_style_summary(),
        "corrections": correction_tracker.get_correction_insights()
    })


@settings_bp.route('/reset', methods=['POST'])
def reset_learning():
    """Reset all learning data (careful!)"""
    data = request.json
    confirm = data.get('confirm', False)
    
    if not confirm:
        return jsonify({"error": "Confirmation required"}), 400
    
    # Reset style JSON
    style_extractor = StyleExtractor()
    style_extractor._style_data = style_extractor._get_default_style()
    style_extractor.save_style()
    
    # Reset vocabulary
    vocab_manager = VocabularyManager()
    vocab_manager.favorite_words = set()
    vocab_manager.favorite_slangs = set()
    vocab_manager.avoided_words = set()
    vocab_manager.word_frequency.clear()
    vocab_manager._save_vocabulary()
    
    return jsonify({"success": True, "message": "Learning data reset"})
