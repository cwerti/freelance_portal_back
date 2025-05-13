from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.general import Review
from schemas.review import ReviewBase, ReviewUpdate

async def get_review(session: AsyncSession, review_id: int):
    result = await session.execute(select(Review).filter(Review.id == review_id))
    return result.scalar_one_or_none()

async def get_reviews_by_reviewed_user(session: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    result = await session.execute(select(Review).filter(Review.reviewed_id == user_id).offset(skip).limit(limit))
    return result.scalars().all()

async def get_reviews_by_reviewer(session: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    result = await session.execute(select(Review).filter(Review.reviewer_id == user_id).offset(skip).limit(limit))
    return result.scalars().all()

async def create_review(session: AsyncSession, review: Review):
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

async def update_review(session: AsyncSession, review_id: int, review: ReviewUpdate):
    result = await session.execute(select(Review).filter(Review.id == review_id))
    db_review = result.scalar_one_or_none()
    
    if not db_review:
        return None
    
    if review.text is not None:
        db_review.text = review.text
    if review.rating is not None:
        db_review.rating = review.rating
    
    await session.commit()  
    await session.refresh(db_review)  
    return db_review

async def delete_review(session: AsyncSession, review_id: int):
    result = await session.execute(select(Review).filter(Review.id == review_id))
    db_review = result.scalar_one_or_none()
    
    if not db_review:
        return None
    
    await session.delete(db_review)  
    await session.commit()  
    return db_review