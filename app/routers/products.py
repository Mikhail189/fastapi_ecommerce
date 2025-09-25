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
from app.models.products import Product
from app.schemas.products import CreateProduct

from app.routers.auth import get_current_user
from app.config import REDIS_CLIENT, WINDOW, RATE_LIMIT, s3_client, S3_BUCKET
import json
from app.mongo_client import log_event
import io
from datetime import datetime

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)],
                        get_user: Annotated[dict, Depends(get_current_user)]):

    #products = await db.scalars(select(Product).where((Product.is_active == True) & (Product.stock > 0))).all()

    cached = await REDIS_CLIENT.get("all_products")
    if cached:
        return json.loads(cached)  # данные лежат в Redis как строка JSON

    result = await db.scalars(
        select(Product).where((Product.is_active == True) & (Product.stock > 0))
    )
    products = result.all()
    if len(products) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )

    products_for_redis = [
        {
            "id": product.id,
            "name": product.name,
            "category_id": product.category_id,
            "slug": product.slug,
            "is_active": product.is_active,
            "price": product.price
        }
        for product in products
    ]
    # 3. Кладём результат в Redis на 60 секунд
    await REDIS_CLIENT.set("all_products", json.dumps(products_for_redis), ex=60)

    # 🔹 пишем факт просмотра в Mongo
    await log_event(
        user_id=get_user["id"],
        action="view_products",
        data={"count": len(products)}
    )

    return products


@router.post('/')
async def create_product(db: Annotated[AsyncSession, Depends(get_db)], create_product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_supplier') or get_user.get('is_admin'):
        category = await db.scalar(select(Category).where(Category.id == create_product.category))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no category found'
            )
        await db.execute(insert(Product).values(name=create_product.name,
                                                description=create_product.description,
                                                price=create_product.price,
                                                image_url=create_product.image_url,
                                                stock=create_product.stock,
                                                category_id=create_product.category,
                                                rating=0.0,
                                                slug=slugify(create_product.name),
                                                supplier_id=get_user.get('id')))
        await db.commit()
        # создаем текстовый файл в памяти
        content = f"Пользователь {get_user['id']} создал продукт {create_product.name} в {datetime.utcnow()}"
        file_obj = io.BytesIO(content.encode("utf-8"))

        # заливаем в S3
        file_key = f"logs/products/{create_product.name}_{datetime.utcnow().isoformat()}.txt"
        s3_client.upload_fileobj(file_obj, S3_BUCKET, file_key)

        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful',
            's3_file': file_key
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You have not enough permission for this action'
        )


@router.get('/{category_slug}/')
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)],
                              category_slug: str):
    category = await db.scalars(select(Category).where(Category.slug == category_slug)).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )
    subcategories = await db.scalars(select(Category).where(Category.parent_id == category.id)).all()
    all_ids = [subcategory.id for subcategory in subcategories]
    all_ids.append(category.id)
    products = await db.scalars(select(Product).where(
        (Product.category_id.in_(all_ids)) & (Product.is_active == True) & (Product.stock > 0))).all()
    return products


@router.get('/detail/{product_slug}')
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)],
                         product_slug: str):
    product = await db.scalars(select(Product).where(Product.slug == product_slug, Product.is_active == True, Product.stock > 0)).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )
    return product


@router.put('/detail/{product_slug}')
async def update_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str,
                         update_product_model: CreateProduct, get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_supplier') or get_user.get('is_admin'):
        product_update = await db.scalar(select(Product).where(Product.slug == product_slug))
        if product_update is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no product found'
            )
        if get_user.get('id') == product_update.supplier_id or get_user.get('is_admin'):
            category = await db.scalar(select(Category).where(Category.id == update_product_model.category))
            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='There is no category found'
                )
            await db.execute(
                update(Product).where(Product.slug == product_slug)
                .values(name=update_product_model.name,
                        description=update_product_model.description,
                        price=update_product_model.price,
                        image_url=update_product_model.image_url,
                        stock=update_product_model.stock,
                        category_id=update_product_model.category,
                        slug=slugify(update_product_model.name)))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'transaction': 'Product update is successful'
            }
        else:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You have not enough permission for this action'
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You have not enough permission for this action'
        )


@router.delete('/')
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    product_delete = await db.scalar(select(Product).where(Product.slug == product_slug))
    if product_delete is None:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no product found'
             )
    if get_user.get('is_supplier') or get_user.get('is_admin'):
        if get_user.get('id') == product_delete.supplier_id or get_user.get('is_admin'):
            await db.execute(update(Product).where(Product.slug == product_slug).values(is_active=False))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'transaction': 'Product delete is successful'
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You have not enough permission for this action'
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You have not enough permission for this action'
        )
