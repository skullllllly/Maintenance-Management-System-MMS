from sqlalchemy import insert,select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ticket_status_history import TicketStatusHistory
from app.schema.ticket_status_history import StatusHistoryCreate
from app.models.user import User
from app.models.ticket import MaintenanceTicket

async def get_by_id(db:AsyncSession,history_id:int)->TicketStatusHistory|None:
    stmt=(
        select(TicketStatusHistory)
        .options(
            selectinload(TicketStatusHistory.ticket),
            selectinload(TicketStatusHistory.changed_by),
        )
        .where(TicketStatusHistory.history_id==history_id)
    )

    result=await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_all(
    db:AsyncSession,
    *,
    skip:int =0,
    limit:int =100,
    ticket_id:int|None=None,
    changed_by_user_id:int |None=None
)->list[TicketStatusHistory]:
    
    stmt=(
        select(TicketStatusHistory)
        .options(
            selectinload(TicketStatusHistory.ticket),
            selectinload(TicketStatusHistory.changed_by),
        )
        .order_by(TicketStatusHistory.changed_at.desc())
        .offset(skip)
        .limit(limit)
    )

    if ticket_id is not None:
        stmt=stmt.where(TicketStatusHistory.ticket_id==ticket_id)
    if changed_by_user_id is not None:
        stmt=stmt.where(TicketStatusHistory.changed_by_user_id==changed_by_user_id)

    result=await db.execute(stmt)
    return list(result.unique().scalars().all())


async def create(db:AsyncSession,payload:StatusHistoryCreate)->TicketStatusHistory:

    if not await db.get(MaintenanceTicket,payload.ticket_id):
        raise ValueError("ticket does not exist")
    if not await db.get(User,payload.changed_by_user_id):
        raise ValueError("user does not exist")

    stmt=(
        insert(TicketStatusHistory)
        .values(**payload.model_dump())
        .returning(TicketStatusHistory.history_id)
    )

    result=await db.execute(stmt)
    await db.commit()

    history_id=result.scalar_one()
    return await get_by_id(db,history_id)
