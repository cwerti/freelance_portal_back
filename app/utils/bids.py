from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from models.general import Order, Bid, Notification, BidStatus
from sqlalchemy import update, func


async def get_order_author_id_by_bid(
    bid_id: int,
    session: AsyncSession
) -> int | None:
    result = await session.execute(
        select(Order.author_id)
        .join(Bid, Bid.order_id == Order.id)
        .where(Bid.id == bid_id)
    )
    return result.scalar_one_or_none()

async def notify_author_about_new_bid(
    bid_id: int,
    session: AsyncSession
):

    author_id = await get_order_author_id_by_bid(bid_id, session)
    
    if not author_id:
        raise ValueError("Автор этого отклика не найден")
    
    notification = Notification(
        user_id=author_id,
        message=f"Новый отклик  (Bid ID: {bid_id})",
        is_read=False
    )
    
    session.add(notification)
    await session.commit()

async def update_order_status_by_bid_id(
    bid_id: int,
    new_status_id: int,
    session: AsyncSession
) -> bool:
    """
    Обновляет статус заказа по ID отклика
    Возвращает True если обновление прошло успешно, False если отклик или заказ не найдены
    """
    result = await session.execute(
        select(Bid, Order)
        .join(Order, Bid.order_id == Order.id)
        .where(Bid.id == bid_id)
        .with_for_update()
    )
        
    bid, order = result.first() or (None, None)
        
    if not order:
        return False
        
    order.status_id = new_status_id
        
    if new_status_id == 2:
        bid.status = BidStatus.ACCEPTED
    
    if new_status_id == 3:
        bid.status = BidStatus.REJECTED
        
    await session.commit()
    return True

async def get_bids_by_user(
    user_id: int,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> list[Bid]:
    result = await session.execute(
        select(Bid)
        .join(Order, Order.id == Bid.order_id)
        .where(Order.author_id == user_id)
        .order_by(Bid.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    return result.scalars().all()

async def update_bid_status_by_bid_id(
    bid_id: int,
    new_status_id: int,
    session: AsyncSession
) -> bool:
    """
    Обновляет статус заказа по ID отклика
    Возвращает True если обновление прошло успешно, False если отклик или заказ не найдены
    """
    result = await session.execute(
        select(Bid, Order)
        .join(Order, Bid.order_id == Order.id)
        .where(Bid.id == bid_id)
        .with_for_update() 
    )
        
    bid, order = result.first() or (None, None)
        
    if not order:
        return False
    
    if not bid:
        return False

    if new_status_id == 2:
        bid.status = BidStatus.ACCEPTED
        order.status_id = 2
    
    if new_status_id == 3:
        bid.status = BidStatus.REJECTED
        
    await session.commit()
    return True

async def reject_other_bids_and_notify(
    order_id: int,
    accepted_bid_id: int,
    session: AsyncSession
):
    rejected_bids = (await session.execute(
            select(Bid)
            .where(Bid.order_id == order_id)
            .where(Bid.status == BidStatus.PENDING)
            )
        ).scalars().all()
    
    if not rejected_bids:
        return
    
    # Обновляем статус и создаем уведомления
    notifications = []
    for bid in rejected_bids:
        bid.status = BidStatus.REJECTED
        notifications.append(
            Notification(
                user_id=bid.user_id,
                message=f"Ваш отклик #{bid.id} был отклонен",
                is_read=False
            )
        )
    
    session.add_all(notifications)
    await session.commit()
