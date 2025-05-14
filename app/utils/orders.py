from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.general import Order
from schemas.order import OrderUpdate
from fastapi import HTTPException, status

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
    skip: int = 0, 
    limit: int = 10,
):
    result = await session.execute(
        select(Order)
        .where(
            Order.status_id == 1
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def get_orders_by_author(
    session: AsyncSession, 
    author_id: int
):
    result = await session.execute(select(Order).where(Order.author_id == author_id))
    return result.scalars().all()