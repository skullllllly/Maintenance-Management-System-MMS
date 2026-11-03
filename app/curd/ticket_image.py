from sqlalchemy import insert,select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ticket_image import TicketImage
from app.schema.ticket_image import TicketImageCreate
from app.models.ticket import MaintenanceTicket

async def get_by_id(db:AsyncSession,image_id:int)->TicketImage|None:

    stmt=(
        select(TicketImage)
        .options(selectinload(TicketImage.ticket))
        .where(TicketImage.image_id==image_id)
    )
    result=await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_all(
    db:AsyncSession,
    *,
    skip:int=0,
    limit:int=100,
    ticket_id:int|None=None
)->list[TicketImage]:

    stmt=(
        select(TicketImage)
        .options(selectinload(TicketImage.ticket))
        .order_by(TicketImage.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
    )

    if ticket_id is not None:
        stmt=stmt.where(MaintenanceTicket.ticket_id==ticket_id)

    result=await db.execute(stmt)
    return list(result.unique().scalars().all())


async def create(db:AsyncSession,payload:TicketImageCreate)->TicketImage:

    ticket=await db.get(MaintenanceTicket,payload.ticket_id)
    if ticket is None:
        raise ValueError("Ticket does not exist")

    duplicate = await db.execute(
        select(TicketImage.image_id).where(
            TicketImage.minio_object_name == payload.minio_object_name
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise ValueError("This object is already attached an image record")

    image=TicketImage(**payload.model_dump())
    db.add(image)
    await db.flush()
    await db.refresh(image)
    return image