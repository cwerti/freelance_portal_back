from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database_connection import db_async_session
from sqlalchemy import select, update
from schemas.bids import BidCreate, BidStatus, NotificationResponse, BidResponse
from models.general import Bid, Order, Notification
from utils.bids import notify_author_about_new_bid, get_bids_by_user, update_bid_status_by_bid_id, reject_other_bids_and_notify
from typing import List

bids = APIRouter()

# Создание отклика
@bids.post("/orders/{order_id}/bids", status_code=status.HTTP_201_CREATED)
async def create_bid(
    order_id: int,
    bid_data: BidCreate,
    session: AsyncSession = Depends(db_async_session),
):
    # Проверка прав
    # if current_user.role != UserRole.FREELANCER:
    #     raise HTTPException(status_code=403, detail="Only freelancers can create bids")
    
    # Проверка заказа
    order = (await session.get(Order, order_id))
    if not order or order.status_id != 1:
        raise HTTPException(status_code=404, detail="Order not available for bidding")

    # Проверка существующего отклика
    existing_bid = (await session.execute(
        select(Bid).where(
            (Bid.order_id == order_id) &
            (Bid.user_id == bid_data.user_id)
        )
    ))

    order_author_id = await session.execute(select(Order.author_id).where(Order.id == order_id))  

    if bid_data.user_id == order_author_id:
        raise HTTPException(status_code=400, detail="You can't leave a bid for yourself.")

    if existing_bid.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="You already have a bid for this order")
    
    # Создание отклика
    new_bid = Bid(
        **bid_data.dict(),
        order_id=order_id
    )
    
    session.add(new_bid)
    await session.commit()
    await notify_author_about_new_bid(new_bid.id, session)
    return new_bid

#  Принятие отклика
@bids.patch("/bids/{bid_id}/accept")
async def accept_bid(
    bid_id: int,
    session: AsyncSession = Depends(db_async_session),
):
    bid = await session.get(Bid, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # # Проверка прав
    # if bid.order.author_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Only order author can accept bids")
    
    await update_bid_status_by_bid_id(bid_id, 2, session)

    await reject_other_bids_and_notify(Bid.order_id, Bid.id, session)
    
    # Создание уведомлений
    notification_accept = Notification(
        user_id=bid.user_id,
        message=f"Your bid was accepted!"
    )
    
    session.add_all([notification_accept, ])
    await session.commit()
    
    return {"message": "Bid accepted successfully"}

@bids.patch("/bids/{bid_id}/reject")
async def reject_bid(
    bid_id: int,
    session: AsyncSession = Depends(db_async_session),
):
    bid = await session.get(Bid, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # # Проверка прав
    # if bid.order.author_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="Only order author can accept bids")
    
    
    await update_bid_status_by_bid_id(bid_id, 3, session)

    order_title = await session.execute(
        select(Order.name)
        .join(Bid, Bid.order_id == Order.id)
        .where(Bid.id == bid_id)
    )
    
    # Создание уведомлений
    notification_user = Notification(
        user_id=bid.user_id,
        message=f"Your bid was rejected."
    )

    
    session.add_all([notification_user])
    await session.commit()
    
    return {"message": "Bid rejected successfully"}

# Получение уведомлений
@bids.get("/notifications", response_model=list[NotificationResponse])
async def get_notifications(
    user_id: int,
    session: AsyncSession = Depends(db_async_session)
):
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    return result.scalars().all()

@bids.get("/by-user/{user_id}", response_model=List[BidResponse])
async def get_bids_for_user(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(db_async_session)
):
        bids = await get_bids_by_user(
            user_id=user_id,
            session=session,
            skip=skip,
            limit=limit
        )
        
        if not bids:
            return {"message": "No bids found for this user"}
            
        return bids