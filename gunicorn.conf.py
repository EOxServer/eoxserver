import os
import multiprocessing

from prometheus_client import multiprocess


chdir = os.environ.get('INSTANCE_DIR', '')
bind = ':8000'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
timeout = 600


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
