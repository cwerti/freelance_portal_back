from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from models.general import Order, Bid, Notification, BidStatus
from sqlalchemy import update


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
    # Получаем author_id заказа, к которому относится отклик
    author_id = await get_order_author_id_by_bid(bid_id, session)
    
    if not author_id:
        raise ValueError("Order author not found for this bid")
    
    # Здесь логика отправки уведомления автору
    notification = Notification(
        user_id=author_id,
        message=f"New bid received for your order (Bid ID: {bid_id})",
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
    # 1. Находим отклик и связанный с ним заказ
    result = await session.execute(
        select(Bid, Order)
        .join(Order, Bid.order_id == Order.id)
        .where(Bid.id == bid_id)
        .with_for_update()  # Блокируем строки для обновления
    )
        
    bid, order = result.first() or (None, None)
        
    if not order:
        return False
        
    # 2. Обновляем статус заказа
    order.status_id = new_status_id
        
    # 3. Если нужно, обновляем статус самого отклика
    if new_status_id == 2:  # Если заказ принят в работу
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
    """
    Получает все отклики (bids) на заказы указанного пользователя (recipient_id)
    
    Args:
        recipient_id: ID пользователя-получателя (author_id в Order)
        session: Асинхронная сессия БД
        skip: Пропуск первых N записей
        limit: Максимальное количество возвращаемых записей
    
    Returns:
        Список откликов (bids) с полной информацией
    """
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
    # 1. Находим отклик и связанный с ним заказ
    result = await session.execute(
        select(Bid, Order)
        .join(Order, Bid.order_id == Order.id)
        .where(Bid.id == bid_id)
        .with_for_update()  # Блокируем строки для обновления
    )
        
    bid, order = result.first() or (None, None)
        
    if not order:
        return False
    
    if not bid:
        return False
        
    # 3. Если нужно, обновляем статус самого отклика
    if new_status_id == 2:  # Если заказ принят в работу
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
    # 1. Находим все отклоняемые отклики
    rejected_bids_result = await session.execute(
        select(Bid)
        .where(Bid.order_id == order_id)
        .where(Bid.id != accepted_bid_id)
        .where(Bid.status == BidStatus.PENDING)  # Только отклики в статусе PENDING
    )
    rejected_bids = rejected_bids_result.scalars().all()

    # 2. Обновляем статус всех отклоняемых откликов
    await session.execute(
        update(Bid)
        .where(Bid.order_id == order_id)
        .where(Bid.id != accepted_bid_id)
        .where(Bid.status == BidStatus.PENDING)
        .values(status=BidStatus.REJECTED)
    )

    # 3. Создаем уведомления для каждого отклоненного отклика
    for bid in rejected_bids:
        notification = Notification(
            user_id=bid.user_id,  # ID пользователя, чей отклик отклонен
            message=f"Your bid #{bid.id} for order {bid.order_id} was rejected",
            is_read=False
        )
        session.add(notification)

    # 4. Фиксируем изменения
    await session.commit()