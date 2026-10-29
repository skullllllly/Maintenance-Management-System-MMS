from sqlalchemy import delete,insert,select,update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.schema.role import RoleCreate,RoleUpdate

async def get_by_id(db:AsyncSession,id_role:int) -> Role|None:
    stmt=(
        select(Role)
        .options(selectinload(Role.users))
        .where(Role.id_role == id_role)
    )
    result =await db.execute(stmt)
    return result.unique().scalar_one_or_none()

async def get_all(
    db:AsyncSession,
    *,
    skip:int =0,
    limit:int =100,
    is_active:bool |None =None,
)->list[Role]:
    stmt=(
        select(Role)
        .options(selectinload(Role.users))
        .order_by(Role.id_role.asc())
        .offset(skip)
        .limit(limit)
    )
    if is_active is not None:
        stmt =stmt.where(Role.is_active == is_active)
    result=await db.execute(stmt)
    return list(result.unique().scalars().all())

async def create(db:AsyncSession,payload:RoleCreate)->Role:
    existing = await db.execute(
        select(Role).where(Role.name_role==payload.name_role)
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("Role name already exist.")

    stmt=(
        insert(Role)
        .values(**payload.model_dump())
        .returning(Role.id_role)
    )
    result=await db.execute(stmt)
    await db.commit()

    id_role=result.scalar_one()
    return await get_by_id(db,id_role)

async def update(
    db:AsyncSession,
    id_role:int ,
    payload:RoleUpdate,
)->Role| None:
    current=await get_by_id(db,id_role)
    if current is None:
        return None

    data=payload.model_dump(exclude_unset=True)
    if not data:
        return current
    
    if "name_role" in data and data["name_role"] is not None:
        duplicate= await db.execute(
            select(Role).where(Role.name_role == data["name_role"])
            )
            if duplicate.scalar_one_or_none() is not None:
                raise ValueError("Role name already exists.")

    stmt =(
        update(Role)
        .where(Role.id_role==id_role)
        .values(**data)

    )
    await db.execute(stmt)
    await db.commit()

    return await get_by_id(db,id_role)

async def delete(db:AsyncSession,id_role:int)->bool:
    stmt=delete(Role).where(Role.id_role== id_role)
    result=await db.execute(stmt)
    await db.commit()
    return result.rowcount>0

