from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGO_URL
from typing import Optional
from pydantic import Field
from datetime import datetime, timezone
from .celery_app import celery_app
import time
from loguru import logger
import logging
import sys
logger.add(sys.stdout, level="DEBUG")


mongo_client = AsyncIOMotorClient(MONGO_URL)
mongo_db = mongo_client["ecommerce_db"]  # Здесь мы выбираем базу данных с именем ecommerce_db
events_collection = mongo_db["events"]  # Выбираем коллекцию (аналог таблицы) с именем events


async def log_event(user_id: int, action: str, data: Optional[dict] = Field(default=None)):
    event = {
        "user_id": user_id,
        "action": action,
        "data": data or {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    try:
        result = await events_collection.insert_one(event)
        logger.info("✅ Mongo inserted with id: %s", result.inserted_id)
        print("Mongo inserted with id:", result.inserted_id)
    except Exception as e:
        print("Mongo insert error:", e)
        logger.error("❌ Mongo insert error: %s", e)


@celery_app.task
def log_event_task(user_id: int, action: str, data: Optional[dict] = Field(default=None)):
    time.sleep(10)
    event = {
        "user_id": user_id,
        "action": action,
        "data": data or {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    # ⛔ Mongo драйвер async, а Celery синхронный — используем .insert_one через sync API
    events_collection.insert_one(event)
    return f"Event logged: {action}"

