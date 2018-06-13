from __future__ import absolute_import, unicode_literals
from celery import Celery

app = Celery('covis_worker',
             broker='amqp://user:bitnami@localhost',
             backend='rpc://',
             include=['covis_worker.sample_tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()
