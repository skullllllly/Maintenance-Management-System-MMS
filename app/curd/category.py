from sqlalchemy import insert,delete,select,update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import TicketCategory
from app.schema.category import CategoryCreate,CategoryUpdate

async def get_by_id(db:AsyncSession,category_id:int)->TicketCategory | None:
    stmt=(
        select(TicketCategory)
        .options(
            selectinload(TicketCategory.tickets)
        )
        .where(TicketCategory.category_id==category_id)
    )

    result=await db.execute(stmt)
    return result.unique().scalar_one_or_none()

async def get_all(
    db:AsyncSession,
    *,
    skip:int=0,
    limit:int=100,
)->list[TicketCategory]:

    stmt=(
        select(TicketCategory)
        .options(
            selectinload(TicketCategory.tickets)
        )
        .order_by(TicketCategory.category_id.asc())
        .offset(skip)
        .limit(limit)
    )
    result=await db.execute(stmt)
    return list(result.unique().scalars().all())


async def create(db:AsyncSession,payload:CategoryCreate)->TicketCategory:
    existing=await db.execute(
        select(TicketCategory).where(TicketCategory.category_name==payload.category_name)
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("Category name already exist")

    stmt=(
        insert(TicketCategory)
        .values(**payload.model_dump())
        .returning(TicketCategory.category_id)

    )
    result= await db.execute(stmt)
    await db.commit()

    category_id=result.scalar_one()
    return await get_by_id(db,category_id)


async def update(db:AsyncSession,category_id:int ,payload:CategoryUpdate)->TicketCategory|None:
    current=await get_by_id(db,category_id)
    if current is  None:
        return None

    data=payload.model_dump(exclude_unset=True)
    if not data:
        return current

    if "category_name" in data and data["category_name"] is not None :
        duplicate=await db.execute(
            select(TicketCategory).where(TicketCategory.category_name==data["category_name"]
            )
        )
        if duplicate.scalar_one_or_none() is not None:
            raise ValueError("Category name already exist")
        
    stmt=(
            update(TicketCategory)
            .where(TicketCategory.category_id==category_id)
            .values(**data)
        )
    result=await db.execute(stmt)
    await db.commit()

    return await get_by_id(db,category_id)

async def delete(db:AsyncSession,category_id)->bool:
    stmt=(
        delete(TicketCategory)
        .where(TicketCategory.category_id==category_id)
    )
    result=await db.execute(stmt)
    await db.commit()

    return result.rowcount > 0