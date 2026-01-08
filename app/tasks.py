"""
Background Tasks
Async task definitions for Celery
"""
from celery import shared_task
from typing import Dict, Optional


@shared_task(bind=True, max_retries=3)
def generate_ai_suggestion(self, session_id: int, action: str = 'next', 
                           current_line: str = '', improvement_type: str = 'rhyme',
                           style: str = None) -> Dict:
    """
    Generate AI suggestion in the background.
    
    Args:
        session_id: Session to generate for
        action: 'next' or 'improve'
        current_line: Line to improve (for improve action)
        improvement_type: Type of improvement
        style: Optional artist style
        
    Returns:
        Dict with suggestion result
    """
    from flask import current_app
    from app.models import LyricSession, UserProfile
    from app.ai import get_provider
    from app.learning import StyleExtractor
    
    try:
        session = LyricSession.query.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        profile = UserProfile.get_or_create_default()
        
        # Get previous lines
        lines = session.lines.all()
        previous_lines = [l.final_version or l.user_input for l in lines]
        
        # Build style context
        style_extractor = StyleExtractor()
        style_context = style_extractor.get_style_summary()
        
        # Add artist style if specified
        if style:
            from app.ai.style_library import get_style_context
            artist_context = get_style_context(style)
            if artist_context:
                style_context.update(artist_context)
        
        provider = get_provider(profile.preferred_provider)
        
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
            return {"error": "Invalid action"}
        
        return {
            "success": True,
            "result": result,
            "session_id": session_id
        }
        
    except Exception as e:
        self.retry(exc=e, countdown=5)
        return {"error": str(e)}


@shared_task(bind=True, max_retries=2)
def transform_line_style(self, line: str, style: str, 
                         session_id: int = None) -> Dict:
    """
    Transform a line to match an artist's style.
    
    Args:
        line: Original line
        style: Artist style key
        session_id: Optional session context
        
    Returns:
        Dict with transformed variations
    """
    from app.models import LyricSession, UserProfile
    from app.ai import get_provider
    from app.ai.style_library import get_style_context
    
    try:
        style_context = get_style_context(style)
        if not style_context:
            return {"error": f"Unknown style: {style}"}
        
        profile = UserProfile.get_or_create_default()
        provider = get_provider(profile.preferred_provider)
        
        # Build transform prompt
        transform_prompt = f"""Transform this lyric line to match {style_context['style_name']}'s style.

Original line: "{line}"

{style_context['style_prompt']}

Provide 3 variations of the transformed line.

Format:
1. [variation 1]
2. [variation 2]
3. [variation 3]"""

        session_context = {}
        if session_id:
            session = LyricSession.query.get(session_id)
            if session:
                session_context = {"bpm": session.bpm, "mood": session.mood}
        
        result = provider.answer_user_question(transform_prompt, session_context)
        
        return {
            "success": True,
            "original": line,
            "style": style_context['style_name'],
            "transformations": result
        }
        
    except Exception as e:
        self.retry(exc=e, countdown=3)
        return {"error": str(e)}


@shared_task(bind=True)
def export_pdf(self, session_id: int) -> Dict:
    """
    Generate PDF export in the background.
    
    Args:
        session_id: Session to export
        
    Returns:
        Dict with path to generated PDF
    """
    import os
    from pathlib import Path
    from app.models import LyricSession, UserProfile
    from app.config import Config
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors
    except ImportError:
        return {"error": "reportlab not installed"}
    
    try:
        session = LyricSession.query.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        lines = session.lines.all()
        profile = UserProfile.get_or_create_default()
        
        # Create export directory
        export_dir = Path(Config.DATA_DIR) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF
        filename = f"session_{session_id}_{session.title.replace(' ', '_')}.pdf"
        filepath = export_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        styles = getSampleStyleSheet()
        
        story = []
        story.append(Paragraph(session.title, styles['Heading1']))
        story.append(Spacer(1, 12))
        
        for line in lines:
            text = line.final_version or line.user_input
            story.append(Paragraph(text, styles['Normal']))
        
        doc.build(story)
        
        return {
            "success": True,
            "path": str(filepath),
            "filename": filename
        }
        
    except Exception as e:
        return {"error": str(e)}


@shared_task(bind=True)
def detect_bpm(self, file_path: str, session_id: int) -> Dict:
    """
    Detect BPM from audio file and update session.
    
    Args:
        file_path: Path to audio file
        session_id: Session to update
        
    Returns:
        Dict with detected BPM
    """
    from app.models import db, LyricSession
    
    try:
        from app.analysis.audio_analyzer import detect_bpm as analyze_bpm
        
        bpm = analyze_bpm(file_path)
        
        if bpm > 0:
            session = LyricSession.query.get(session_id)
            if session:
                session.bpm = bpm
                db.session.commit()
        
        return {
            "success": True,
            "bpm": bpm,
            "session_id": session_id
        }
        
    except Exception as e:
        return {"error": str(e)}


@shared_task(bind=True)
def reindex_search(self) -> Dict:
    """
    Rebuild the entire search index.
    
    Returns:
        Dict with reindex statistics
    """
    try:
        from app.search import get_search_index
        
        search_index = get_search_index()
        stats = search_index.reindex_all()
        
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        return {"error": str(e)}
