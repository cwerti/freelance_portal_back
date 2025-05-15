from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from utils.orders import create_order, get_order, get_orders, delete_order, update_order, get_active_orders, get_orders_by_author, get_all_categories, search_orders_by_name
from schemas.order import OrderModel, OrderUpdate, OrderOut, CategoryOut
from utils.database_connection import db_async_session


orders = APIRouter()

@orders.post("/")
async def order_create(
        order: OrderModel,
        session: AsyncSession = Depends(db_async_session)
    ):
    return await create_order(session=session, order=order)

@orders.get("/by-order/{order_id}")
async def order_get(
        order_id: int,
        session: AsyncSession = Depends(db_async_session)
    ):
    return await get_order(session=session, order_id=order_id)

@orders.get("/orders")
async def get_order_list(
        session: AsyncSession = Depends(db_async_session),
        skip: int = 0,
        limit: int = 10
    ):
    return await get_orders(session=session, skip=skip, limit=limit)

@orders.get("/active")
async def get_active_orders_route(
    category_id: Optional[int] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    deadline_from: Optional[datetime] = None,
    deadline_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = Query(10, le=100),
    session: AsyncSession = Depends(db_async_session)
):
    return await get_active_orders(
        session=session,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        deadline_from=deadline_from,
        deadline_to=deadline_to,
        skip=skip,
        limit=limit
    )

@orders.get("/by-author/{user_id}")
async def get_order_list_active(
        author_id: int,
        session: AsyncSession = Depends(db_async_session),
    ):
    orders = await get_orders_by_author(session, author_id)
    if not orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orders found for this author"
        )
    return orders
@orders.delete("/{order_id}")
async def order_delete(
        order_id: int,
        session: AsyncSession = Depends(db_async_session)
    ):
    return await delete_order(session=session, order_id=order_id)

@orders.put("/update")
async def update_order_route(
        order_id: int, 
        order_update: OrderUpdate,
        session: AsyncSession = Depends(db_async_session)
    ):
    return await update_order(session, order_id, order_update)

@orders.get("/categories", response_model=list[CategoryOut])
async def read_categories(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(db_async_session)
):
    return await get_all_categories(session, skip, limit)

@orders.get("/search/", response_model=list[OrderOut])
async def search_orders(
    q: str = Query(..., min_length=1, max_length=50, description="Search query"),
    category_id: Optional[int] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    skip: int = 0,
    limit: int = Query(10, le=100),
    session: AsyncSession = Depends(db_async_session)
) -> list[OrderOut]:
    return await search_orders_by_name(
        session=session,
        search_query=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        skip=skip,
        limit=limit
    )
