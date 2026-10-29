from sqlalchemy import delete,insert,select,update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.user import User
from app.schema.user import UserCreate,UserUpdate

from app.core.security import hash_password

async def get_by_id(db:AsyncSession,user_id:int) ->User |None:
    stmt=(
        select(User)
        .options(
            selectinload(User.role),
            selectinload(User.reported_tickets),
            selectinload(User.assigned_tickets),
            selectinload(User.status_changes),
            selectinload(User.maintenance_logs),
            selectinload(User.assessments)
        )
        .where(User.user_id == user_id)

    )
    result=await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_all(
    db:AsyncSession,
    *,
    skip:int=0,
    limit:int=100,
    id_role:int |None=None,
    is_active:bool|None=None,
)->list[User]:

    stmt=(
        select(User)
        .options(selectinload(User.role))
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        
    )
    if id_role is not None:
        stmt = stmt.where(User.id_role==id_role)
    if is_active is not None:
        stmt=stmt.where(User.is_active==is_active)

    result =await db.execute(stmt)
    return list(result.unique().scalars().all())

async def create(db:AsyncSession, payload:UserCreate)->User:
    if not await db.get(Role,payload.id_role):
        raise ValueError("Role does not exist.")

    email_exists=await db.execute(
        select(User).where(User.email==payload.email)
    )
    if email_exists.scalar_one_or_none() is not None:
        raise ValueError("email already registered")

    phone_exists=await db.execute(
        select(User).where(User.phone_number==payload.phone_number)
    )
    if phone_exists.scalar_one_or_none() is not None:
        raise ValueError("phone number already registered")
    
 
     

    values=payload.model_dump(exclude={"password"})
    values["password_hash"]=hash_password(payload.password)

    stmt=insert(User).values(**values).returning(User.user_id)
    result=await db.execute(stmt)
    await db.commit()

    user_id=result.scalar_one_or_none()
    return await get_by_id(db,user_id)

async def update(
    db:AsyncSession,
    user_id:int,
    payload:UserUpdate,
)->User|None :

    current=await get_by_id(db,user_id)
    if current is None:
        return None

    data=payload.model_dump(exclude_unset=True)
    if not data:
        return current

    if "password" in data and data["password"] is not None:
        data["password_hash"]= hash_password(data.pop("password"))

    if "id_role" in data and data["id_role"] is not None:
        if not await db.get(Role,data["id_role"]):
            raise ValueError("Role does not exist.")

    if "email" in data and data["email"] is not None:
        existing_email=await db.execute(
            select(User).where(User.email==data["email"],User.user_id !=user_id)
        )
        if existing_email.scalar_one_or_none() is not None:
            raise ValueError("email already registered")

    if "phone_number" in data and data["phone_number"] is not None:
        existing_phone=await db.execute(
            select(User).where(
                User.phone_number==data["phone_number"],
                User.user_id !=user_id,
            )
        )
        if existing_phone.scalar_one_or_none() is not None:
            raise ValueError("phone number already registered")
    stmt=(
        update(User)
        .where(User.user_id==user_id)
        .values(**data)
    )
    await db.execute(stmt)
    await db.commit()

    return await get_by_id(db,user_id)

async def delete(db:AsyncSession,user_id:int)->bool:
    stmt=delete(User).where(User.user_id==user_id)
    result=await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
