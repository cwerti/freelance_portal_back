from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from models.general import Order
from schemas.order import OrderUpdate
from fastapi import HTTPException, status
from datetime import datetime
from typing import Optional

async def create_order(session: AsyncSession, order: Order):
    db_order = Order(
        author_id=order.author_id,
        name=order.name,
        description=order.description,
        start_price=order.start_price, 
        category_id=order.category_id
    )
    session.add(db_order)
    await session.commit()  
    await session.refresh(db_order)  
    return db_order

async def get_order(session: AsyncSession, order_id: int):
    result = await session.execute(select(Order).filter(Order.id == order_id))
    return result.scalar_one_or_none()

async def delete_order(session: AsyncSession, order_id: int):
    result = await session.execute(select(Order).filter(Order.id == order_id))
    db_order = result.scalar_one_or_none()
    
    if not db_order:
        return None
    
    await session.delete(db_order)  
    await session.commit()
    return db_order

async def get_orders(session: AsyncSession, skip: int = 0, limit: int = 10):
    result = await session.execute(select(Order).offset(skip).limit(limit))
    return result.scalars().all()

async def update_order(
    session: AsyncSession, 
    order_id: int, 
    order_update: OrderUpdate
):
    """
    Обновляет заказ по ID
    """
    result = await session.execute(select(Order).filter(Order.id == order_id))
    db_order = result.scalar_one_or_none()
        
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
        
    update_data = order_update.dict(exclude_unset=True)
    for field, value in update_data.items():
            setattr(db_order, field, value)
        
    await session.commit()
    await session.refresh(db_order)
    return db_order
    
async def get_active_orders(
    session: AsyncSession,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    deadline_from: Optional[datetime] = None,
    deadline_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 10,
):
    query = select(Order).where(Order.status_id == 1)
        
    if category_id is not None:
        query = query.where(Order.category_id == category_id)
        
    if min_price is not None or max_price is not None:
        price_filters = []
        if min_price is not None:
            price_filters.append(Order.start_price >= min_price)
        if max_price is not None:
            price_filters.append(Order.start_price <= max_price)
        query = query.where(and_(*price_filters))
            
    if deadline_from is not None or deadline_to is not None:
        deadline_filters = []
        if deadline_from is not None:
            deadline_filters.append(Order.deadline >= deadline_from)
        if deadline_to is not None:
            deadline_filters.append(Order.deadline <= deadline_to)
        query = query.where(and_(*deadline_filters))
        
    query = query.offset(skip).limit(limit)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    result = await session.execute(query)
    return result.scalars().all()

async def get_orders_by_author(
    session: AsyncSession, 
    author_id: int
):
    result = await session.execute(select(Order).where(Order.author_id == author_id))
    return result.scalars().all()
