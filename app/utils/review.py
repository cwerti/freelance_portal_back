from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.general import Review
from schemas.review import ReviewBase
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from models.general import User



async def get_review(session: AsyncSession, review_id: int):
    try:
        result = await session.execute(select(Review).filter(Review.id == review_id))
        review = result.scalar_one_or_none()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with id {review_id} not found"
            )
        return review
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

async def get_reviews_by_reviewed_user(session: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    try:
        result = await session.execute(
            select(Review)
            .filter(Review.reviewed_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

async def get_reviews_by_reviewer(session: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    result = await session.execute(
        select(Review)
        .filter(Review.reviewer_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def create_review(session: AsyncSession, review: Review):
    db_review = Review(
        comment=review.comment,
        rating=review.rating,
        reviewer_id=review.reviewer_id, 
        reviewed_id=review.reviewed_id
    )
    reviewer_id = db_review.reviewer_id
    reviewed_id = db_review.reviewed_id
    client_exists = await session.get(User, reviewer_id)
    executor_exists = await session.get(User, reviewed_id)
    
    if not all([client_exists, executor_exists]):
        raise HTTPException(
            status_code=401,
            detail="Client or executor not found"
        )
    existing_review = await session.execute(
        select(Review).where(
            (Review.reviewer_id == review.reviewer_id) &
            (Review.reviewed_id == review.reviewed_id)
        )
    )
    existing_review = existing_review.scalar_one_or_none()
    if existing_review:
        # Обновляем существующий отзыв
        existing_review.comment = review.comment
        existing_review.rating = review.rating
        await session.commit()
        await session.refresh(existing_review)
        return existing_review
    else:
        # Создаем новый отзыв
        db_review = Review(
            comment=review.comment,
            rating=review.rating,
            reviewer_id=review.reviewer_id, 
            reviewed_id=review.reviewed_id
        )
        session.add(db_review)
        await session.commit()
        await session.refresh(db_review)
        return db_review

async def update_review(session: AsyncSession, review_id: int, review: ReviewBase):
    try:
        result = await session.execute(select(Review).filter(Review.id == review_id))
        db_review = result.scalar_one_or_none()
        
        if not db_review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with id {review_id} not found"
            )

        if review.text is not None:
            db_review.text = review.text
        if review.rating is not None:
            db_review.rating = review.rating
        
        await session.commit()  
        await session.refresh(db_review)  
        return db_review
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while updating review: {str(e)}"
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating review: {str(e)}"
        )

async def delete_review(session: AsyncSession, review_id: int):
    try:
        result = await session.execute(select(Review).filter(Review.id == review_id))
        db_review = result.scalar_one_or_none()
        
        if not db_review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with id {review_id} not found"
            )
        
        await session.delete(db_review)  
        await session.commit()  
        return db_review
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while deleting review: {str(e)}"
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting review: {str(e)}"
        )