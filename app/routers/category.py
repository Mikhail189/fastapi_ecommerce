from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing_extensions import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update

from slugify import slugify

from app.backend.db_depends import get_db
from app.schemas.category import CreateCategory
from app.models.category import Category

from app.routers.auth import get_current_user
from app.config import REDIS_CLIENT, WINDOW, RATE_LIMIT
import json
from app.mongo_client import log_event

router = APIRouter(prefix='/categories', tags=['category'])


@router.get('/')
async def get_all_categories(db: Annotated[AsyncSession, Depends(get_db)],
                             get_user: Annotated[dict, Depends(get_current_user)]):
    # 1. Проверяем кэш
    user_id = get_user["id"]
    key = f"rate_limit:user:{user_id}"
    #print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
    # 2. Увеличиваем счётчик
    current = await REDIS_CLIENT.incr(key)
    if current == 1:
        # если ключ только что создан — выставим TTL
        await REDIS_CLIENT.expire(key, WINDOW)

    # 3. Проверяем лимит
    if current > RATE_LIMIT:
        ttl = await REDIS_CLIENT.ttl(key)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {ttl} seconds."
        )

    cached = await REDIS_CLIENT.get("all_categories")
    if cached:
        return json.loads(cached)  # данные лежат в Redis как строка JSON

    # 2. Если кэша нет — идём в БД
    categories_ = await db.scalars(select(Category).where(Category.is_active == True))
    categories = categories_.all()
    categories_for_redis = [
        {
            "id": cat.id,
            "name": cat.name,
            "parent_id": cat.parent_id,
            "slug": cat.slug,
            "is_active": cat.is_active,
        }
        for cat in categories
    ]
    # 3. Кладём результат в Redis на 60 секунд
    await REDIS_CLIENT.set("all_categories", json.dumps(categories_for_redis), ex=60)

    # 🔹 пишем факт просмотра в Mongo
    await log_event(
        user_id=get_user["id"],
        action="view_categories",
        data={"count": len(categories)}
    )

    return categories


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_category(db: Annotated[AsyncSession, Depends(get_db)],
                          create_category: CreateCategory,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_admin'):
        await db.execute(insert(Category).values(name=create_category.name,
                                           parent_id=create_category.parent_id,
                                           slug=slugify(create_category.name)))
        await db.commit()

        await REDIS_CLIENT.delete("all_categories")

        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this'
        )


@router.put('/')
async def update_category(db: Annotated[AsyncSession, Depends(get_db)], category_id: int,
                          update_category: CreateCategory, get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_admin'):
        category = await db.scalar(select(Category).where(Category.id == category_id))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no category found'
            )

        await db.execute(update(Category).where(Category.id == category_id).values(
            name=update_category.name,
            slug=slugify(update_category.name),
            parent_id=update_category.parent_id))

        await db.commit()
        await REDIS_CLIENT.delete("all_categories")
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Category update is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this'
        )


@router.delete('/')
async def delete_category(db: Annotated[AsyncSession, Depends(get_db)], category_id: int,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_admin'):
        category = await db.scalar(select(Category).where(Category.id == category_id))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no category found'
            )
        await db.execute(update(Category).where(Category.id == category_id).values(is_active=False))
        await db.commit()
        await REDIS_CLIENT.delete("all_categories")
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Category delete is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this'
        )
