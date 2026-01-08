"""
Streaming API Routes
Endpoints that return Server-Sent Events (SSE) for real-time AI generation
"""
from flask import Blueprint, Response, stream_with_context, request, jsonify
from app.models import LyricSession, UserProfile
from app.ai import get_provider
from app.schemas import SuggestLineRequest
from pydantic import ValidationError
import json

streaming_bp = Blueprint('streaming', __name__)

@streaming_bp.route('/api/line/stream', methods=['GET'])
def stream_suggestion():
    """Stream AI suggestion for next line"""
    session_id = request.args.get('session_id')
    current_line = request.args.get('current_line', '')
    
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
        
    session = LyricSession.query.get_or_404(session_id)
    profile = UserProfile.get_or_create_default()
    
    # Get provider
    try:
        provider = get_provider(profile.preferred_provider)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    def generate():
        # Build context (similar to standard suggest)
        lines = session.lines.all()
        previous_lines = [l.final_version or l.user_input for l in lines]
        style_context = {"streaming": True}
        
        try:
            # Call streaming method on provider
            stream = provider.suggest_next_line_stream(
                previous_lines=previous_lines,
                bpm=session.bpm,
                style_context=style_context
            )
            
            for chunk in stream:
                # SSE format: "data: <content>\n\n"
                clean_chunk = chunk.replace('\n', ' ') # Avoid breaking SSE format with newlines
                yield f"data: {clean_chunk}\n\n"
                
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')
