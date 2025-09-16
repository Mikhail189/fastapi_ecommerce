from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing_extensions import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update

from slugify import slugify

from app.backend.db_depends import get_db
from app.models.review import Review
from app.models.rating import Rating
from app.models.products import Product

from app.schemas.review import CreateReview
from app.schemas.rating import CreateRating

from app.routers.auth import get_current_user


router = APIRouter(prefix='/review_rating', tags=['review_rating'])


@router.get('/')
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews_scalar = await db.scalars(select(Review).where(Review.is_active == True))
    reviews = reviews_scalar.all()
    if len(reviews) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no reviews'
        )
    return reviews


@router.get('/{prodict_id}')
async def products_reviews(db: Annotated[AsyncSession, Depends(get_db)],
                         product_id: int):
    reviews_scalar = await db.scalars(select(Review).where(Review.product_id == product_id, Review.is_active == True))
    reviews = reviews_scalar.all()
    if reviews is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )
    for review in reviews:
        rating_scalar = await db.scalars(select(Rating).where(Rating.id == review.rating_id, Rating.is_active == True))
        rating = rating_scalar.first()
        review.rating = rating.grade

    return reviews


@router.post('/')
async def add_review(db: Annotated[AsyncSession, Depends(get_db)],
                     get_user: Annotated[dict, Depends(get_current_user)],
                     create_review: CreateReview,
                     create_rating: CreateRating):
    if get_user.get('is_customer'):
        product = await db.scalar(select(Product).where(Product.id == create_rating.product_id))
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no product found'
            )
        rating = await db.execute(insert(Rating).values(grade=create_rating.grade,
                                                        user_id=get_user.get('id'),
                                                        product_id=create_rating.product_id,
                                                        is_active=True
                                                        ).returning(Rating.id))
        rating_id = rating.scalar()

        await db.execute(insert(Review).values(user_id=get_user.get('id'),
                                               product_id=create_review.product_id,
                                               rating_id=rating_id,
                                               comment=create_review.comment,
                                               comment_date=create_review.comment_date.replace(tzinfo=None),
                                               is_active=True
                                               ))

        product_grade = await db.scalars(select(Rating.grade).where(Rating.product_id == create_rating.product_id))
        product_grade_list = product_grade.all()
        average_grade = sum(product_grade_list) / len(product_grade_list)
        await db.execute(update(Product).where(Product.id == create_rating.product_id).values(rating=average_grade))

        await db.commit()
        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You have not enough permission for this action'
        )


@router.delete('/')
async def delete_reviews(db: Annotated[AsyncSession, Depends(get_db)], rating_id: int,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    rating_delete = await db.scalar(select(Rating).where(Rating.id == rating_id))
    if rating_delete is None:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no rating found'
             )
    if get_user.get('is_supplier') or get_user.get('is_admin'):
        await db.execute(update(Rating).where(Rating.id == rating_id).values(is_active=False))
        await db.execute(update(Review).where(Review.rating_id == rating_id).values(is_active=False))
        await db.commit()
        return  {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You have not enough permission for this action'
        )







