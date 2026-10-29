from sqlalchemy import insert,select,delete,update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payment import Payment
from app.schema.payment import PaymentCreate,PaymentUpdate
from app.models.ticket import MaintenanceTicket

async def get_by_id(db:AsyncSession,payment_id:int)->Payment|None:
    stmt=(
        select(Payment)
        .options(selectinload(Payment.ticket))
        .where(Payment.payment_id==payment_id)
    )
    result=await db.execute(stmt)
    return result.unique().scalar_one_or_none()

async def get_all(
    db:AsyncSession,
    *,
    skip:int=0,
    limit:int=100,
    ticket_id:int|None=None
)->list[Payment]:
    stmt=(
        select(Payment)
        .options(selectinload(Payment.ticket))
        .order_by(Payment.paid_at.desc().nulls_last())
        .offset(skip)
        .limit(limit)
    )

    if ticket_id is not None:
        stmt=stmt.where(Payment.ticket_id==ticket_id)
    
    result=await db.execute(stmt)
    return list(result.unique().scalars().all())


async def create(db:AsyncSession,payload:PaymentCreate)->Payment:
    if not await db.get(MaintenanceTicket,payload.ticket_id):
        raise ValueError("Ticket does not exist ")

    existing=await db.execute(
        select(Payment).where(Payment.ticket_id==payload.ticket_id)
    )
    
    if existing.scalar_one_or_none() is not None:
        raise ValueError("payment already exists for this ticket ")

    stmt=(
        insert(Payment)
        .values(**payload.model_dump())
        .returning(Payment.payment_id)
    )

    result=await db.execute(stmt)
    await db.commit()

    payment_id=result.scalar_one()
    return await get_by_id(db,payment_id)


async def update(db:AsyncSession,payment_id:int,payload:PaymentUpdate)->Payment|None:
    current=await get_by_id(db,payment_id)
    
    if current is None:
        return None
    
    data=payload.model_dump(exclude_unset=True)
    
    if not data:
        return current

    stmt=(
        update(Payment)
        .where(Payment.payment_id==payment_id)
        .values(**data)
    )
    await db.execute(stmt)
    await db.commit()

    return await get_by_id(db,payment_id)

async def delete(db:AsyncSession,payment_id:int)->bool:
    stmt=(
        delete(Payment)
        .where(Payment.payment_id==payment_id)
    )
    result=await db.execute(stmt)
    await db.commit()
    
    return result.rowcount > 0