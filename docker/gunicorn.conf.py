import os
import multiprocessing


chdir = os.environ.get('INSTANCE_DIR', '')
bind = ':8000'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
timeout = 600
