from __future__ import absolute_import, unicode_literals
from celery import Celery

from decouple import config

app = Celery('covis_worker',
             broker=config('CELERY_BROKER', default='amqp://user:bitnami@localhost'),
             backend=config('CELERY_BACKEND', default='rpc://'),
             include=['covis_worker.process', 'covis_worker.rezip'])

app.broker_connection_timeout = 30

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
