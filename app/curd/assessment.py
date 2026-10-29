from sqlalchemy import insert,delete,update,select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import Assessment
from app.schema.assessment import AssessmentCreate,AssessmentUpdate
from app.models.user import User
from app.models.ticket import MaintenanceTicket

async def get_by_id(db:AsyncSession,assignment_id:int)->Assessment|None:

    stmt=(
        select(Assessment)
        .options(
            selectinload(Assessment.ticket),
            selectinload(Assessment.technician)
        )
        .where(Assessment.assignment_id==assignment_id)
    )
    result=await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_all(
    db:AsyncSession,
    *,
    skip:int=0,
    limit:int =100,
    ticket_id:int|None=None,
    technician_id:int|None=None
)->list[Assessment]:

    stmt=(
        select(Assessment)
        .options(
            selectinload(Assessment.ticket),
            selectinload(Assessment.technician) 
        )
        .order_by(Assessment.assigned_at.desc())
        .offset(skip)
        .limit(limit)
    )

    if ticket_id is not None :
        stmt=stmt.where(Assessment.ticket_id==ticket_id)
    if technician_id is not None:
        stmt=stmt.where(Assessment.technician_id==technician_id)

    result=await db.execute(stmt)
    return list(result.unique().scalars().all())

async def create(db:AsyncSession,payload:AssessmentCreate)->Assessment:

    if not await db.get(MaintenanceTicket,payload.ticket_id):
        raise ValueError("ticket does not exist")
    if not await db.get(User,payload.technician_id):
        raise ValueError("Technician does not exist ")
    
    existing=await db.execute(
        select(Assessment).where(Assessment.ticket_id==payload.ticket_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("this ticket already has an assignment")

    stmt=(
        insert(Assessment)
        .values(**payload.model_dump())
        .returning(Assessment.assignment_id)
    )
    result=await db.execute(stmt)
    await db.commit()

    assignment_id=result.scalar_one()
    return await get_by_id(db,assignment_id)

async def update(db:AsyncSession,assignment_id:int,payload:AssessmentUpdate)->Assessment|None:

    existing=await get_by_id(db,assignment_id)
    if existing is None:
        return None

    data=payload.model_dump(exclude_unset=True)
    if not data:
        return existing

    if "technician_id" in data and data["technician_id"] is not None:
        if not await db.get(User,data["technician_id"]):
            raise ValueError("Technician does not exist")

    stmt=(
        update(Assessment)
        .where(Assessment.assignment_id==assignment_id)
        .values(**data)
    )
    await db.execute(stmt)
    await db.commit

    return await get_by_id(db,assignment_id)


async def delete(db:AsyncSession,assignment_id:int)->bool:
    stmt=(
        delete(Assessment)
        .where(Assessment.assignment_id==assignment_id)

    )
    result=await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

    