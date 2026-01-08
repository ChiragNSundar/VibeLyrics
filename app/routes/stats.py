"""
Stats Routes
Writing statistics dashboard and analytics
"""
from flask import Blueprint, render_template, jsonify
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import Counter

from app.models import db, LyricSession, LyricLine, UserProfile

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/')
def index():
    """Stats dashboard page"""
    profile = UserProfile.get_or_create_default()
    return render_template('stats.html', profile=profile)


@stats_bp.route('/api/overview')
def get_overview():
    """Get overview statistics"""
    # Total counts
    total_sessions = LyricSession.query.count()
    total_lines = LyricLine.query.count()
    
    # Calculate total words
    all_lines = LyricLine.query.with_entities(LyricLine.final_version, LyricLine.user_input).all()
    total_words = sum(
        len((line.final_version or line.user_input or "").split()) 
        for line in all_lines
    )
    
    # Average BPM
    avg_bpm = db.session.query(func.avg(LyricSession.bpm)).scalar() or 140
    
    # Unique vocabulary
    all_text = " ".join(
        (line.final_version or line.user_input or "").lower() 
        for line in all_lines
    )
    words = [w.strip('.,!?;:\'"()-[]') for w in all_text.split() if len(w) > 2]
    unique_words = len(set(words))
    
    # Sessions this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    sessions_this_week = LyricSession.query.filter(
        LyricSession.created_at >= week_ago
    ).count()
    
    # Lines today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    lines_today = LyricLine.query.filter(
        LyricLine.created_at >= today_start
    ).count()
    
    # Complexity average
    avg_complexity = db.session.query(
        func.avg(LyricLine.complexity_score)
    ).filter(LyricLine.complexity_score.isnot(None)).scalar() or 0
    
    return jsonify({
        "success": True,
        "stats": {
            "total_sessions": total_sessions,
            "total_lines": total_lines,
            "total_words": total_words,
            "unique_vocabulary": unique_words,
            "avg_bpm": round(avg_bpm),
            "sessions_this_week": sessions_this_week,
            "lines_today": lines_today,
            "avg_complexity": round(avg_complexity * 100) if avg_complexity else 0
        }
    })


@stats_bp.route('/api/history')
def get_history():
    """Get time-series data for charts"""
    # Lines per day for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    lines = LyricLine.query.filter(
        LyricLine.created_at >= thirty_days_ago
    ).with_entities(LyricLine.created_at).all()
    
    # Group by date
    lines_by_day = Counter()
    for line in lines:
        date_str = line.created_at.strftime('%Y-%m-%d')
        lines_by_day[date_str] += 1
    
    # Fill in missing days
    daily_data = []
    for i in range(30):
        date = (datetime.utcnow() - timedelta(days=29-i)).strftime('%Y-%m-%d')
        daily_data.append({
            "date": date,
            "lines": lines_by_day.get(date, 0)
        })
    
    # Vocabulary growth (cumulative unique words over time)
    sessions = LyricSession.query.order_by(LyricSession.created_at).all()
    vocab_growth = []
    seen_words = set()
    
    for session in sessions:
        for line in session.lines.all():
            text = (line.final_version or line.user_input or "").lower()
            words = [w.strip('.,!?;:\'"()-[]') for w in text.split() if len(w) > 2]
            seen_words.update(words)
        
        vocab_growth.append({
            "session": session.title[:20],
            "date": session.created_at.strftime('%Y-%m-%d'),
            "vocabulary": len(seen_words)
        })
    
    return jsonify({
        "success": True,
        "daily_lines": daily_data,
        "vocabulary_growth": vocab_growth[-20:] if len(vocab_growth) > 20 else vocab_growth
    })


@stats_bp.route('/api/rhyme_schemes')
def get_rhyme_schemes():
    """Get most used rhyme schemes"""
    from app.analysis import RhymeDetector
    
    rhyme_detector = RhymeDetector()
    scheme_counts = Counter()
    
    sessions = LyricSession.query.limit(50).all()  # Last 50 sessions
    
    for session in sessions:
        lines = [l.final_version or l.user_input for l in session.lines.all()]
        if len(lines) >= 4:
            scheme = rhyme_detector.get_rhyme_scheme_string(lines[:8])
            if scheme:
                scheme_counts[scheme] += 1
    
    top_schemes = scheme_counts.most_common(5)
    
    return jsonify({
        "success": True,
        "schemes": [{"scheme": s, "count": c} for s, c in top_schemes]
    })


@stats_bp.route('/api/achievements')
def get_achievements():
    """Get user achievements/badges"""
    total_lines = LyricLine.query.count()
    total_sessions = LyricSession.query.count()
    
    # Calculate streak
    today = datetime.utcnow().date()
    streak = 0
    current_date = today
    
    while True:
        day_start = datetime.combine(current_date, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        
        lines_that_day = LyricLine.query.filter(
            LyricLine.created_at >= day_start,
            LyricLine.created_at < day_end
        ).count()
        
        if lines_that_day > 0:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
        
        if streak > 365:  # Cap at 1 year
            break
    
    achievements = []
    
    # Line milestones
    if total_lines >= 10:
        achievements.append({"name": "First Steps", "icon": "🌱", "desc": "Write 10 lines"})
    if total_lines >= 50:
        achievements.append({"name": "Getting Warmed Up", "icon": "🔥", "desc": "Write 50 lines"})
    if total_lines >= 100:
        achievements.append({"name": "Century", "icon": "💯", "desc": "Write 100 lines"})
    if total_lines >= 500:
        achievements.append({"name": "Prolific", "icon": "📚", "desc": "Write 500 lines"})
    if total_lines >= 1000:
        achievements.append({"name": "Legendary", "icon": "👑", "desc": "Write 1000 lines"})
    
    # Session milestones
    if total_sessions >= 5:
        achievements.append({"name": "Session Master", "icon": "🎯", "desc": "Complete 5 sessions"})
    if total_sessions >= 20:
        achievements.append({"name": "Album Ready", "icon": "💿", "desc": "Complete 20 sessions"})
    
    # Streak achievements
    if streak >= 3:
        achievements.append({"name": "On Fire", "icon": "🔥", "desc": "3 day streak"})
    if streak >= 7:
        achievements.append({"name": "Week Warrior", "icon": "⚔️", "desc": "7 day streak"})
    if streak >= 30:
        achievements.append({"name": "Monthly Master", "icon": "🏆", "desc": "30 day streak"})
    
    return jsonify({
        "success": True,
        "achievements": achievements,
        "current_streak": streak,
        "total_lines": total_lines,
        "total_sessions": total_sessions
    })
