from sqlalchemy import insert,select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.route import RoutLog
from app.schema.route import RouteLogCreate
from app.models.assessment import Assessment

async def get_by_id(db:AsyncSession,route_id:int)->RoutLog|None:

    stmt=(
        select(RouteLog)
        .options(selectinload(RouteLog.assessment))
        .where(RouteLog.route_id==route_id)
    )
    result=await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_all(
    db:AsyncSession,
    *,
    skip:int=0,
    limit:int=100,
    assignment_id:int|None=None
)->list[RouteLog]:

    stmt=(
        select(RouteLog)
        .options(selectinload(RouteLog.assessment))
        .order_by(RouteLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if assignment_id is not None:
        stmt=stmt.where(RouteLog.assignment_id==assignment_id)

    result=await db.execute(stmt)
    return list(result.unique().scalars().all())

async def create(db:AsyncSession,payload:RouteLogCreate)->RouteLog:

    if not await db.get(Assessment,payload.assignment_id):
        raise ValueError("assignment does not exist")

    stmt=(
        insert(RouteLog)
        .values(**payload.model_dump())
        .returning(RouteLog.route_id)
    )

    result=await db.execute(stmt)
    await db.commit()

    route_id=result.scalar_one()
    return await get_by_id(db,route_id)