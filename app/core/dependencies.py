from typing import Annotated

from fastapi import Depends,HTTPException,status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token,oauth2_scheme
from app.db.session import get_db
from app.models.user import User


async def get_current_user_id(
    token:Annotated[str,Depends(oauth2_scheme)],
)->int:

    payload= decode_access_token(token)
    user_id= payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="Token missing Subject",
            headers={"WWW-Authenticate" : "Bearer"},
        )

    try:
        return int(user_id)
    except(TypeError,ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subjetc",
            headers={"WWW-Authenticate" : "Bearer"},
        )from exc


async def get_current_user(
    db:Annotated[AsyncSession,Depends(get_db)],
    user_id: Annotated[int,Depends(get_current_user_id)],
)->User:
    stmt = select(User).where(User.user_id==user_id)
    result= await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail= "User not found ",
            headers={"WWW-Authenticate" : "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user ",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

async def get_current_active_user(
    current_user:Annotated[User,Depends(get_current_user)]
)->User:

    if not current_user.is_active :
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate":"Bearer"}
        )

    return current_user

    