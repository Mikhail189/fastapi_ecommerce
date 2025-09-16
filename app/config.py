import os
import redis.asyncio as redis

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres_user:postgres_password@185.250.44.62:5432/postgres_database"
)

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres_user:postgres_password@185.250.44.62:5433/postgres_test_database"
)

REDIS_CLIENT = redis.from_url("redis://:password_redis_1488@redis:6379", decode_responses=True)

RATE_LIMIT = 5   # максимум запросов
WINDOW = 20      # окно в секундах

MONGO_URL = "mongodb://admin_1488:secret_1488@mongo:27017/?authSource=admin"