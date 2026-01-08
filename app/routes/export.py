"""
Export Routes
Export lyrics in various formats (PDF, TXT, Teleprompter)
"""
from flask import Blueprint, render_template, Response, jsonify, make_response
from io import BytesIO
from datetime import datetime

from app.models import LyricSession, LyricLine, UserProfile
from app.analysis import RhymeDetector

export_bp = Blueprint('export', __name__)


@export_bp.route('/<int:session_id>/txt')
def export_txt(session_id):
    """Export session as plain text file"""
    session = LyricSession.query.get_or_404(session_id)
    lines = session.lines.all()
    
    # Build text content
    content_lines = [
        f"# {session.title}",
        f"# BPM: {session.bpm} | Mood: {session.mood or 'N/A'} | Theme: {session.theme or 'N/A'}",
        f"# Date: {session.created_at.strftime('%Y-%m-%d')}",
        "",
    ]
    
    current_section = None
    for line in lines:
        if line.section != current_section:
            current_section = line.section
            content_lines.append(f"\n[{current_section}]")
        content_lines.append(line.final_version or line.user_input)
    
    content = "\n".join(content_lines)
    
    # Create response
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{session.title}.txt"'
    
    return response


@export_bp.route('/<int:session_id>/pdf')
def export_pdf(session_id):
    """Export session as styled PDF"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        return jsonify({"error": "reportlab not installed. Run: pip install reportlab"}), 500
    
    session = LyricSession.query.get_or_404(session_id)
    lines = session.lines.all()
    profile = UserProfile.get_or_create_default()
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=12,
        textColor=colors.HexColor('#8b5cf6')
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=24
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=18,
        spaceAfter=6,
        textColor=colors.HexColor('#06b6d4')
    )
    
    line_style = ParagraphStyle(
        'LineStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=18,
        fontName='Courier'
    )
    
    # Build document content
    story = []
    
    # Title
    story.append(Paragraph(session.title, title_style))
    
    # Metadata
    meta_text = f"BPM: {session.bpm} | Mood: {session.mood or 'N/A'} | Theme: {session.theme or 'N/A'}<br/>"
    meta_text += f"Written by: {profile.name} | Date: {session.created_at.strftime('%Y-%m-%d')}"
    story.append(Paragraph(meta_text, meta_style))
    
    story.append(Spacer(1, 0.25*inch))
    
    # Lyrics with sections
    current_section = None
    
    for line in lines:
        if line.section != current_section:
            current_section = line.section
            story.append(Paragraph(f"[{current_section}]", section_style))
        
        text = line.final_version or line.user_input
        # Escape XML special characters
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(text, line_style))
    
    # Build PDF
    doc.build(story)
    
    # Return PDF
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{session.title}.pdf"'
    
    return response


@export_bp.route('/<int:session_id>/teleprompter')
def export_teleprompter(session_id):
    """Teleprompter view with large scrolling text"""
    session = LyricSession.query.get_or_404(session_id)
    lines = session.lines.all()
    
    return render_template('teleprompter.html', session=session, lines=lines)


@export_bp.route('/<int:session_id>/json')
def export_json(session_id):
    """Export session as JSON (for backup/import)"""
    session = LyricSession.query.get_or_404(session_id)
    lines = session.lines.all()
    
    data = {
        "title": session.title,
        "bpm": session.bpm,
        "mood": session.mood,
        "theme": session.theme,
        "created_at": session.created_at.isoformat(),
        "lines": [
            {
                "number": line.line_number,
                "section": line.section,
                "text": line.final_version or line.user_input,
                "syllables": line.syllable_count
            }
            for line in lines
        ]
    }
    
    response = make_response(jsonify(data))
    response.headers['Content-Disposition'] = f'attachment; filename="{session.title}.json"'
    
    return response
