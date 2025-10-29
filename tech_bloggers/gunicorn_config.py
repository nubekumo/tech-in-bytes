"""
Gunicorn configuration file for production deployment.
"""

import multiprocessing
import os

# Server socket
bind = "unix:/var/www/techinbytes/gunicorn.sock"  # Unix socket for Nginx communication
# Alternative: bind = "0.0.0.0:8000"  # TCP socket

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended formula
worker_class = 'sync'  # Can be 'gevent' or 'eventlet' for async
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 50  # Add randomness to max_requests to avoid all workers restarting at once
timeout = 30  # Worker timeout in seconds
keepalive = 2  # Keep connections alive for this many seconds

# Logging
accesslog = '/var/www/techinbytes/logs/gunicorn-access.log'
errorlog = '/var/www/techinbytes/logs/gunicorn-error.log'
loglevel = 'info'  # debug, info, warning, error, critical
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'tech_bloggers'

# Server mechanics
daemon = False  # Run in foreground when using systemd
pidfile = '/var/www/techinbytes/gunicorn.pid'
user = None  # Set by systemd service
group = None  # Set by systemd service
umask = 0o007  # Umask for file permissions
tmp_upload_dir = None  # Use default temp directory

# Security
limit_request_line = 4094  # Max size of HTTP request line
limit_request_fields = 100  # Max number of HTTP headers
limit_request_field_size = 8190  # Max size of HTTP header field

# Performance tuning
preload_app = True  # Load application code before forking workers (saves memory)

