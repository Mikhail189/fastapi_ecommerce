import asyncio
import redis.asyncio as redis

async def main():
    r = redis.from_url("redis://localhost:6379", decode_responses=True) #Создаём клиент Redis и подключаемся к серверу,
    # который крутится локально (localhost) на стандартном порту 6379
    # decode_responses=True — делает так, чтобы клиент возвращал строки (str), а не байты (b"...")
    try:
        # ex=10 → TTL (time-to-live) = 10 секунд. Через 10 секунд этот ключ автоматически исчезнет из Redis.
        await r.set("mykey", "Hello Redis!", ex=50)
        value = await r.get("mykey")
        print("VALUE:", value)
        pong = await r.ping()
        print("PING:", pong)
    finally:
        await r.close()  # <-- добавляем

asyncio.run(main())
