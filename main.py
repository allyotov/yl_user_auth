from email.generator import DecodedGenerator
import logging

import redis
import uvicorn
from fastapi import FastAPI

from src.api.v1.resources import posts, users
from src.core import config
from src.db import cache, redis_cache, db
from src.models.post import Post
from src.models.user import User, BlockedAccessToken

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info(config.POSTGRES_HOST)


app = FastAPI(
    # Конфигурируем название проекта. Оно будет отображаться в документации
    title=config.PROJECT_NAME,
    version=config.VERSION,
    # Адрес документации в красивом интерфейсе
    docs_url="/api/openapi",
    redoc_url="/api/redoc",
    # Адрес документации в формате OpenAPI
    openapi_url="/api/openapi.json",
)


@app.get("/")
def root():
    return {"service": config.PROJECT_NAME, "version": config.VERSION}


@app.on_event("startup")
def startup():
    """Подключаемся к базам при старте сервера"""
    print('Создаем базу!')
    db.init_db()


    logger.debug(config.POSTGRES_HOST)
    logger.debug(config.POSTGRES_PORT)
    logger.debug(config.REDIS_HOST)
    logger.debug(config.REDIS_PORT)
    cache.cache = redis_cache.CacheRedis(
        cache_instance=redis.Redis(
            host=config.REDIS_HOST, port=config.REDIS_PORT, max_connections=10, db=1
        )
    )
    logger.debug(cache.cache.cache)
    cache.cache.cache.ping()
    cache.blocked_access_tokens_cache = redis_cache.CacheRedis(
        cache_instance=redis.Redis(
            host=config.REDIS_HOST, port=config.REDIS_PORT, db=2, decode_responses=True
        )
    )
    logger.debug(cache.blocked_access_tokens_cache.cache)
    cache.active_refresh_tokens_cache = redis_cache.CacheRedis(
        cache_instance=redis.Redis(
            host=config.REDIS_HOST, port=config.REDIS_PORT, db=3, decode_responses=True
        )
    )
    logger.debug(cache.active_refresh_tokens_cache.cache)

@app.on_event("shutdown")
def shutdown():
    """Отключаемся от баз при выключении сервера"""
    logger.debug('Сервер выключается. Отключаемся от баз.')
    cache.cache.close()
    cache.blocked_access_tokens_cache.cache.close()
    cache.active_refresh_tokens_cache.cache.close()


# Подключаем роутеры к серверу
app.include_router(router=posts.router, prefix="/api/v1/posts")
app.include_router(router=users.router, prefix="/api/v1")


if __name__ == "__main__":
    # Приложение может запускаться командой
    # `uvicorn main:app --host 0.0.0.0 --port 8000`
    # но чтобы не терять возможность использовать дебагер,
    # запустим uvicorn сервер через python
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
    )
