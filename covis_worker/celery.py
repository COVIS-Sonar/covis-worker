from __future__ import absolute_import, unicode_literals
from celery import Celery

from decouple import config

app = Celery('covis_worker',
             broker=config('CELERY_BROKER', default='amqp://user:bitnami@localhost'),
             backend=config('CELERY_BACKEND', default='rpc://'),
             include=['covis_worker.process', 'covis_worker.rezip'])

# app.broker_connection_timeout = 30
# app.concurrency = 1
# app.worker_prefetch_multiplier = 1
# app.task_acks_late = True

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
    concurrency=1,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_timeout=30
)

if __name__ == '__main__':
    app.start()
