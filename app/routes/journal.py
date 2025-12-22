"""
Journal Routes
Thought capture and context building
"""
import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.models import db, JournalEntry
from app.ai import get_provider
from app.models import UserProfile

journal_bp = Blueprint('journal', __name__)


@journal_bp.route('/')
def index():
    """Journal main page"""
    entries = JournalEntry.query.order_by(JournalEntry.created_at.desc()).all()
    return render_template('journal.html', entries=entries)


@journal_bp.route('/add', methods=['POST'])
def add_entry():
    """Add a new journal entry"""
    content = request.form.get('content', '').strip()
    mood = request.form.get('mood', '')
    tags = request.form.get('tags', '')
    
    if not content:
        return jsonify({"error": "Content required"}), 400
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(',') if t.strip()]
    
    entry = JournalEntry(
        content=content,
        mood=mood if mood else None,
        tags=json.dumps(tag_list)
    )
    
    db.session.add(entry)
    db.session.commit()
    
    # Extract themes with AI (async would be better, but keeping simple)
    try:
        profile = UserProfile.get_or_create_default()
        provider = get_provider(profile.preferred_provider)
        extraction = provider.extract_themes_from_journal(content)
        
        entry.extracted_themes = json.dumps(extraction.get('themes', []))
        entry.extracted_keywords = json.dumps(extraction.get('keywords', []))
        if not mood and extraction.get('mood'):
            entry.mood = extraction.get('mood')
        
        db.session.commit()
    except Exception:
        pass  # Theme extraction is optional
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "success": True,
            "entry_id": entry.id
        })
    
    return redirect(url_for('journal.index'))


@journal_bp.route('/quick-add', methods=['POST'])
def quick_add():
    """Quick add a thought via AJAX"""
    data = request.json
    content = data.get('content', '').strip()
    mood = data.get('mood', '')
    
    if not content:
        return jsonify({"error": "Content required"}), 400
    
    entry = JournalEntry(
        content=content,
        mood=mood if mood else None
    )
    
    db.session.add(entry)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "entry": {
            "id": entry.id,
            "content": entry.content,
            "mood": entry.mood
        }
    })


@journal_bp.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry_ajax(entry_id):
    """Delete a journal entry via AJAX"""
    entry = JournalEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"success": True})


@journal_bp.route('/<int:entry_id>/delete', methods=['POST'])
def delete_entry(entry_id):
    """Delete a journal entry"""
    entry = JournalEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": True})
    
    return redirect(url_for('journal.index'))


@journal_bp.route('/<int:entry_id>')
def view_entry(entry_id):
    """View a single journal entry"""
    entry = JournalEntry.query.get_or_404(entry_id)
    
    themes = []
    keywords = []
    tags = []
    
    try:
        themes = json.loads(entry.extracted_themes) if entry.extracted_themes else []
        keywords = json.loads(entry.extracted_keywords) if entry.extracted_keywords else []
        tags = json.loads(entry.tags) if entry.tags else []
    except json.JSONDecodeError:
        pass
    
    return render_template('journal_entry.html', 
                         entry=entry,
                         themes=themes,
                         keywords=keywords,
                         tags=tags)


@journal_bp.route('/search')
def search():
    """Search journal entries"""
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('journal.index'))
    
    # Search in content, mood, and tags
    entries = JournalEntry.query.filter(
        db.or_(
            JournalEntry.content.ilike(f'%{query}%'),
            JournalEntry.mood.ilike(f'%{query}%'),
            JournalEntry.tags.ilike(f'%{query}%'),
            JournalEntry.extracted_themes.ilike(f'%{query}%')
        )
    ).order_by(JournalEntry.created_at.desc()).all()
    
    return render_template('journal.html', entries=entries, search_query=query)


@journal_bp.route('/api/entries')
def api_entries():
    """API endpoint to get journal entries for session context"""
    limit = request.args.get('limit', 5, type=int)
    mood = request.args.get('mood', '')
    
    query = JournalEntry.query
    
    if mood:
        query = query.filter(JournalEntry.mood == mood)
    
    entries = query.order_by(JournalEntry.created_at.desc()).limit(limit).all()
    
    return jsonify([{
        "id": e.id,
        "content": e.content[:200] + "..." if len(e.content) > 200 else e.content,
        "mood": e.mood,
        "created_at": e.created_at.isoformat() if e.created_at else None
    } for e in entries])
