from flask_socketio import emit, join_room, leave_room
from . import socketio, db
from .models import LyricSession, LyricLine
from .analysis import RhymeDetector, SyllableCounter

@socketio.on('join')
def on_join(data):
    session_id = data.get('session_id')
    room = f"session_{session_id}"
    join_room(room)

@socketio.on('leave')
def on_leave(data):
    session_id = data.get('session_id')
    room = f"session_{session_id}"
    leave_room(room)

@socketio.on('update_line')
def handle_update_line(data):
    """
    Handle real-time line updates.
    data = { 'session_id': 1, 'line_id': 123, 'content': 'new text' }
    """
    session_id = data.get('session_id')
    line_id = data.get('line_id')
    content = data.get('content')
    
    line = LyricLine.query.get(line_id)
    if line:
        # Update DB
        line.user_input = content
        line.final_version = content # Sync for now
        
        # Recalculate basic stats
        counter = SyllableCounter()
        analysis = counter.analyze_flow(content)
        line.syllable_count = analysis['total_syllables']
        db.session.commit()
        
        socketio.emit('line_updated', {
            'line_id': line_id,
            'content': content,
            'syllable_count': line.syllable_count,
            'stress_pattern': analysis['stress_pattern']
        }, room=f"session_{session_id}", include_self=True)

@socketio.on('new_line')
def handle_new_line(data):
    """
    Handle new line creation via socket
    """
    session_id = data.get('session_id')
    content = data.get('content')
    section = data.get('section', 'Verse')
    
    session = LyricSession.query.get(session_id)
    if session:
        # Get next line number
        last_line = LyricLine.query.filter_by(session_id=session_id).order_by(LyricLine.line_number.desc()).first()
        next_num = (last_line.line_number + 1) if last_line else 1
        
        counter = SyllableCounter()
        analysis = counter.analyze_flow(content)
        
        new_line = LyricLine(
            session_id=session_id,
            line_number=next_num,
            user_input=content,
            section=section,
            syllable_count=analysis['total_syllables']
        )
        db.session.add(new_line)
        db.session.commit()
        
        # Calculate rhyme highlights and internal rhymes
        session_lines = LyricLine.query.filter_by(session_id=session_id).order_by(LyricLine.line_number).all()
        text_lines = [l.final_version or l.user_input for l in session_lines]
        
        rhyme_detector = RhymeDetector()
        highlighted_texts = rhyme_detector.highlight_lyrics(text_lines)
        
        # Get the new line's highlight (it's the last one)
        new_line_highlight = highlighted_texts[-1] if highlighted_texts else content
        
        # Check internal rhyme for the new line
        # analyze_flow might return it, strictly create properties if needed
        # But RhymeDetector also checks internal rhyming usually?
        # Let's trust RhymeDetector logic or simple check
        # Assuming has_internal_rhyme is not easily available from highlight_lyrics return
        # But we can calculate it or just leave as default for now if complex.
        # Actually SyllableCounter might have done it? No.
        # Let's stick to highlight.
        
        socketio.emit('line_added', {
            'id': new_line.id,
            'line_number': new_line.line_number,
            'content': content,
            'highlighted_html': new_line_highlight,
            'section': section,
            'syllable_count': new_line.syllable_count,
            'stress_pattern': analysis['stress_pattern'],
            'has_internal_rhyme': False # Placeholder or calc if possible.
        }, room=f"session_{session_id}", include_self=True)
