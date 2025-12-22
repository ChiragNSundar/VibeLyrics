"""
Workspace Routes
Main lyric writing workspace
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.models import db, LyricSession, LyricLine, UserProfile
from app.ai import get_provider
from app.analysis import RhymeDetector, SyllableCounter, BPMCalculator
from app.learning import StyleExtractor

workspace_bp = Blueprint('workspace', __name__)


@workspace_bp.route('/')
def index():
    """Main workspace page"""
    # Get recent sessions
    sessions = LyricSession.query.order_by(LyricSession.updated_at.desc()).limit(10).all()
    profile = UserProfile.get_or_create_default()
    
    return render_template('workspace.html', 
                         sessions=sessions,
                         profile=profile)


@workspace_bp.route('/session/new', methods=['POST'])
def new_session():
    """Create a new writing session"""
    title = request.form.get('title', 'Untitled')
    bpm = request.form.get('bpm', 140, type=int)
    mood = request.form.get('mood', '')
    theme = request.form.get('theme', '')
    
    session = LyricSession(
        title=title,
        bpm=bpm,
        mood=mood if mood else None,
        theme=theme if theme else None
    )
    
    db.session.add(session)
    db.session.commit()
    
    return redirect(url_for('workspace.edit_session', session_id=session.id))


@workspace_bp.route('/session/<int:session_id>')
def edit_session(session_id):
    """Edit a writing session"""
    session = LyricSession.query.get_or_404(session_id)
    lines = session.lines.all()
    profile = UserProfile.get_or_create_default()
    
    # Get BPM info
    bpm_calc = BPMCalculator()
    bpm_info = bpm_calc.get_syllable_target(session.bpm)
    
    return render_template('session.html',
                         session=session,
                         lines=lines,
                         profile=profile,
                         bpm_info=bpm_info)


@workspace_bp.route('/session/<int:session_id>/delete', methods=['POST'])
def delete_session(session_id):
    """Delete a session"""
    session = LyricSession.query.get_or_404(session_id)
    db.session.delete(session)
    db.session.commit()
    
    return redirect(url_for('workspace.index'))


@workspace_bp.route('/session/<int:session_id>/update', methods=['POST'])
def update_session(session_id):
    """Update session metadata"""
    session = LyricSession.query.get_or_404(session_id)
    
    session.title = request.form.get('title', session.title)
    session.bpm = request.form.get('bpm', session.bpm, type=int)
    session.mood = request.form.get('mood', session.mood)
    session.theme = request.form.get('theme', session.theme)
    
    db.session.commit()
    
    return jsonify({"success": True})
@workspace_bp.route('/session/<int:session_id>/upload_audio', methods=['POST'])
def upload_audio(session_id):
    """Upload an audio file for the beat player"""
    session = LyricSession.query.get_or_404(session_id)
    
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        import os
        from werkzeug.utils import secure_filename
        
        # Ensure directory exists
        upload_folder = os.path.join('app', 'static', 'uploads', 'audio')
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = secure_filename(f"session_{session_id}_{file.filename}")
        file.save(os.path.join(upload_folder, filename))
        
        session.audio_path = f"uploads/audio/{filename}"
        db.session.commit()
        
        return jsonify({"success": True, "audio_path": url_for('static', filename=session.audio_path)})


@workspace_bp.route('/session/<int:session_id>/upload_recording', methods=['POST'])
def upload_recording(session_id):
    """Upload a vocal recording"""
    session = LyricSession.query.get_or_404(session_id)
    
    if 'recording_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['recording_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        import os
        import json
        from werkzeug.utils import secure_filename
        
        # Ensure directory exists
        upload_folder = os.path.join('app', 'static', 'uploads', 'recordings')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Use timestamp in filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = secure_filename(f"rec_{session_id}_{timestamp}.webm")
        file.save(os.path.join(upload_folder, filename))
        
        # Update session recordings list
        try:
            recordings = json.loads(session.recordings)
        except:
            recordings = []
            
        recordings.append(f"uploads/recordings/{filename}")
        session.recordings = json.dumps(recordings)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "recording_path": url_for('static', filename=recordings[-1]),
            "filename": filename
        })
        

@workspace_bp.route('/session/<int:session_id>/export/print')
def export_print(session_id):
    """Export lyrics for print/PDF"""
    session = LyricSession.query.get_or_404(session_id)
    lines = session.lines.all()
    profile = UserProfile.get_or_create_default()
    
    return render_template('export_print.html',
                         session=session,
                         lines=lines,
                         profile=profile)

