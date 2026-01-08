"""
Gunicorn Configuration for VibeLyrics
Production-ready settings with eventlet for WebSocket support
"""
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
# Using eventlet for WebSocket support with Flask-SocketIO
worker_class = "eventlet"
workers = 1  # Single worker for eventlet (handles async internally)
worker_connections = 1000
timeout = 120
keepalive = 5

# Process naming
proc_name = "vibelyrics"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Environment
raw_env = []

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Graceful shutdown
graceful_timeout = 30

# SSL (uncomment for HTTPS)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"

def on_starting(server):
    """Called just before the master process is initialized."""
    pass

def on_exit(server):
    """Called just before exiting Gunicorn."""
    pass

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    pass
