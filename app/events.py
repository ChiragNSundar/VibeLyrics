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
        
        socketio.emit('line_added', {
            'id': new_line.id,
            'line_number': new_line.line_number,
            'content': content,
            'section': section,
            'syllable_count': new_line.syllable_count,
            'stress_pattern': analysis['stress_pattern']
        }, room=f"session_{session_id}")
