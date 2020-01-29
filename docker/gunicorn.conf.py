import multiprocessing


chdir = ''
bind = ':8000'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'eventlet'
timeout = 600
