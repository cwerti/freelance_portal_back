from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.review import ReviewModel, ReviewBase
from utils.review import ( 
    create_review, 
    get_review, 
    get_reviews_by_reviewed_user,
    update_review as update_review_db,
    delete_review as delete_review_db
)
from utils.database_connection import db_async_session

reviews = APIRouter(tags=["reviews"])

@reviews.post("/")
async def review_create(
    review: ReviewModel,
    session: AsyncSession = Depends(db_async_session)
):
    return await create_review(session=session, review=review)

@reviews.get("/{review_id}")
async def read_review(
    review_id: int,
    session: AsyncSession = Depends(db_async_session)
):
    session_review = await get_review(session, review_id=review_id)
    if session_review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return session_review

@reviews.get("/user/{user_id}")
async def read_reviews_for_user(
    user_id: int,
    session: AsyncSession = Depends(db_async_session),
    skip: int = 0,
    limit: int = 10
):
    return await get_reviews_by_reviewed_user(session, user_id=user_id, skip=skip, limit=limit)

@reviews.put("/{review_id}")
async def update_review(
    review_id: int,
    review: ReviewBase,
    session: AsyncSession = Depends(db_async_session)
):
    session_review = await get_review(session, review_id=review_id)
    if session_review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # if session_review.reviewer_id != current_user.id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You can only update your own reviews"
    #     )
    
    return await update_review_db(session=session, review_id=review_id, review=review)

@reviews.delete("/{review_id}")
async def delete_review(
    review_id: int,
    session: AsyncSession = Depends(db_async_session)
):
    session_review = await get_review(session, review_id=review_id)
    if session_review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # if session_review.reviewer_id != current_user.id and not current_user.is_superuser:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You can only delete your own reviews"
    #     )
    
    await delete_review_db(session=session, review_id=review_id)
    return {"detail": "Review deleted successfully"}