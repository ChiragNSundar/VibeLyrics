from flask import request
from flask_socketio import emit, join_room, leave_room
from . import socketio, db
from .models import LyricSession, LyricLine
from .analysis import RhymeDetector, SyllableCounter

@socketio.on('join')
def on_join(data):
    session_id = data.get('session_id')
    room = f"session_{session_id}"
    join_room(room)
    # emit('status', {'msg': f'User has entered the room {room}.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    session_id = data.get('session_id')
    room = f"session_{session_id}"
    leave_room(room)
    # emit('status', {'msg': 'User has left the room.'}, room=room)

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
        line.syllable_count = counter.count_syllables(content)
        db.session.commit()
        
        # Broadcast to room (exclude sender ideally, but for simplicity broadcast all)
        # Using broadcast=True sends to everyone including sender, helpful for confirmation
        # But for text input, echo can be annoying. 
        # Better: broadcast=True, include_self=False
        socketio.emit('line_updated', {
            'line_id': line_id,
            'content': content,
            'syllable_count': line.syllable_count
        }, room=f"session_{session_id}", include_self=False)

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
        
        new_line = LyricLine(
            session_id=session_id,
            line_number=next_num,
            user_input=content,
            section=section,
            syllable_count=counter.count_syllables(content)
        )
        db.session.add(new_line)
        db.session.commit()
        
        # Real-time rhyme highlighting for the new line?
        # To do this robustly, we'd need to re-analyze context.
        # For now, let's just send the raw line and let client render or simple hgihlight
        
        # BUT wait, user wants robustness. Let's do a quick highlight check against previous line
        # This is hard to do perfectly on single line isolated, but we can try.
        # Better: Just send the data, client reloads or appends.
        
        socketio.emit('line_added', {
            'id': new_line.id,
            'line_number': new_line.line_number,
            'content': content,
            'section': section,
            'syllable_count': new_line.syllable_count
        }, room=f"session_{session_id}")
