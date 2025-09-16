from celery import Celery

celery_app = Celery(
    "ecommerce",
    broker="redis://:password_redis_1488@redis:6379/1",   # Redis база №1 для очередей
    backend="redis://:password_redis_1488@redis:6379/1",   # можно хранить результаты (необязательно)
    include=["app.mongo_client"]
)