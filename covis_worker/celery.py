from __future__ import absolute_import, unicode_literals
from celery import Celery

app = Celery('covis-worker',
             broker='amqp://user:bitnami@localhost/',
             backend='amqp://user:bitnami@localhost/',
             include=['covis_worker.example_tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
