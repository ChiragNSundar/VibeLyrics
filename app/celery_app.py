"""
Celery Application Configuration
Background task queue with Redis broker
"""
import os
from celery import Celery

# Redis URL from environment or default
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'vibelyrics',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # Task routing
    task_routes={
        'app.tasks.generate_ai_suggestion': {'queue': 'ai'},
        'app.tasks.transform_line_style': {'queue': 'ai'},
        'app.tasks.export_pdf': {'queue': 'export'},
        'app.tasks.detect_bpm': {'queue': 'audio'},
        'app.tasks.reindex_search': {'queue': 'maintenance'},
    },
    
    # Rate limiting for AI tasks
    task_annotations={
        'app.tasks.generate_ai_suggestion': {'rate_limit': '10/m'},
        'app.tasks.transform_line_style': {'rate_limit': '10/m'},
    }
)


def init_celery(app):
    """
    Initialize Celery with Flask app context.
    Call this in create_app().
    """
    class FlaskTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery_app.Task = FlaskTask
    return celery_app
