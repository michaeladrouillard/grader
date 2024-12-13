# gunicorn.conf.py
timeout = 300  # 5 minutes instead of default 30 seconds
workers = 1    # Reduce memory usage
threads = 2
worker_class = 'gthread'
bind = "0.0.0.0:10000"
timeout = 120  # Increased timeout for longer grading operations