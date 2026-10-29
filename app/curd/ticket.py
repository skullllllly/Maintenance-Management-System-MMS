from sqlalchemy import insert,delete,update,select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ticket import MaintenanceTicket
from app.schema.ticket import TicketCreate,TicketUpdate
from app.models.user import User
from app.models.category import TicketCategory

async def get_by_id(db:AsyncSession,ticket_id:int)->MaintenanceTicket | None:
    stmt=(
        select(MaintenanceTicket)
        .options(
            selectinload(MaintenanceTicket.category),
            selectinload(MaintenanceTicket.reporter),
            selectinload(MaintenanceTicket.assigned_technician),
            selectinload(MaintenanceTicket.status_history),
            selectinload(MaintenanceTicket.maintenance_logs),
            selectinload(MaintenanceTicket.images),
            selectinload(MaintenanceTicket.assessment),
            selectinload(MaintenanceTicket.payment),
        )
        .where(MaintenanceTicket.ticket_id==ticket_id)
    )
    result=await db.execute(stmt)
    return result.unique().scalar_one_or_none

async def get_all(
    db:AsyncSession,
    *,
    skip: int =0,
    limit:int =100,
    category_id:int |None=None,
    reporter_id:int|None=None,
    assigned_technician_id:int|None=None
)->list[MaintenanceTicket]:

    stmt=(
        select(MaintenanceTicket)
        .options(
            selectinload(MaintenanceTicket.category),
            selectinload(MaintenanceTicket.reporter),
            selectinload(MaintenanceTicket.assigned_technician),
        )
        #from new date to old date (desc)
        .order_by(MaintenanceTicket.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    if category_id is not None:
        stmt=stmt.where(MaintenanceTicket.category_id==category_id)
    if reporter_id is not None:
        stmt=stmt.where(MaintenanceTicket.reporter_id==reporter_id)
    if assigned_technician_id is not None:
        stmt=stmt.where(MaintenanceTicket.assigned_technician_id==assigned_technician_id)

    result=await db.execute(stmt)
    return list(result.unique().scalars().all())


async def create(db:AsyncSession,payload:TicketCreate)->MaintenanceTicket:
    if not await db.get(TicketCategory,payload.category_id):
        raise ValueError("Category does not exist.")
    if not await db.get(User,payload.reporter_id):
        raise ValueError("Reporter does not exist.")
    
    stmt=(
        insert(MaintenanceTicket)
        .values(**payload.model_dump())
        .returning(MaintenanceTicket.ticket_id)
    )
    result=await db.execute(stmt)
    await db.commit()

    ticket_id=result.scalar_one()
    return await get_by_id(db,ticket_id)


async def update(db:AsyncSession,ticket_id:int,payload:TicketUpdate)->MaintenanceTicket|None:
    current=await get_by_id(db,ticket_id)
    if current is None:
        return None

    data=payload.model_dump(exclude_unset=True)
    if not data:
        return current
    
    if "category_id" in data and data["category_id"] is not None:
        if not await db.get(TicketCategory,data["category_id"]):
            raise ValueError("Category does not exist")

    if "assigned_technician_id" in data and data["assigned_technician_id"] is not None:
        if not await db.get(User,data["assigned_technician_id"]):
            raise ValueError("Assigned Technician does not exist")

    stmt=(
        update(MaintenanceTicket)
        .where(MaintenanceTicket.ticket_id==ticket_id)
        .values(**data)
    )
    await db.execute(stmt)
    await db.commit()

    return await get_by_id(db,ticket_id)

async def delete(db:AsyncSession,ticket_id:int)->bool:
    stmt=(
        delete(MaintenanceTicket)
        .where(MaintenanceTicket.ticket_id==ticket_id)
        
    )
    result=await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0