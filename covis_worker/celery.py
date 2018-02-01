from __future__ import absolute_import, unicode_literals
from celery import Celery
from os import getenv

app = Celery('covis-worker',
             broker=getenv("COVIS_CELERY_BROKER",'amqp://user:bitnami@rabbitmq/'),
             backend=getenv("COVIS_CELERY_BACKEND",'amqp://user:bitnami@rabbitmq/'),
             include=['covis_worker.example_tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
