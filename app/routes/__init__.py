"""
Routes package initialization
"""
from .workspace import workspace_bp
from .journal import journal_bp
from .references import references_bp
from .settings import settings_bp
from .api import api_bp

__all__ = [
    'workspace_bp',
    'journal_bp',
    'references_bp',
    'settings_bp',
    'api_bp'
]
