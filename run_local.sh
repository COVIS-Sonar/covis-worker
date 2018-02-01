COVIS_CELERY_BROKER="amqp://user:bitnami@localhost/" celery -A covis_worker worker -l info

