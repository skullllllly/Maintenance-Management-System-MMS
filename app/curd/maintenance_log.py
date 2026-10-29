from sqlalchemy import insert,select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.maintenance_log import MaintenanceLog
from app.schema.maintenance_log import MaintenanceLogCreate
from app.models.user import User
from app.models.ticket import MaintenanceTicket

async def get_by_id(db:AsyncSession,log_id:int)->MaintenanceLog|None:
    stmt=(
        select(MaintenanceLog)
        .options(
            selectinload(MaintenanceLog.ticket),
            selectinload(MaintenanceLog.technician)
        )
        .where(MaintenanceLog.log_id==log_id)

    )
    result=await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_all(
    db:AsyncSession,
    *,
    skip:int=0,
    limit:int=100,
    ticket_id:int |None=None,
    technician_id:int|None=None
)->list[MaintenanceLog]:

    stmt=(
        select(MaintenanceLog)
        .options(
            selectinload(MaintenanceLog.ticket),
            selectinload(MaintenanceLog.technician)
        )
        .order_by(MaintenanceLog.logged_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    if ticket_id is not None:
        stmt=stmt.where(MaintenanceLog.ticket_id==ticket_id)
    if technician_id is not None:
        stmt=stmt.where(MaintenanceLog.technician_id==technician_id)

    result=await db.execute(stmt)
    return list(result.unique().scalars().all())

async def create(db:AsyncSession,payload:MaintenanceLogCreate)->MaintenanceLog:

    if not await db.get(MaintenanceTicket,payload.ticket_id):
        raise ValueError("ticket does not exist")
    if not await db.get(User,payload.technician_id):
        raise ValueError("user does not exist")

    stmt=(
        insert(MaintenanceLog)
        .values(**payload.model_dump())
        .returning(MaintenanceLog.log_id)
    ) 
    result=await db.execute(stmt)
    await db.commit()

    log_id=result.scalar_one()
    return await get_by_id(db,log_id)



