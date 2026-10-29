from passlib.context import CryptContext
from datetime import datetime,timedelta,timezone
from typing import Any

from fastapi import HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError,jwt
from pydantic import BaseModel

from app.core.config import settings

#password hashing 
pwd_context=CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

#OAuth2 schema for bearar tokens
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login")

#JWT setting 
JWT_SECRET_KEY=settings.JWT_SECRET_KEY
JWT_ALGORITHM=settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES=settings.ACCESS_TOKEN_EXPIRE_MINUTES

def hash_password(password:str)->str:
    if not password:
        raise ValueError("password can not be empty")
    
    return pwd_context.hash(password)

def verify_password(plain_password:str,hashed_password:str)->bool:
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password,hashed_password)

#token key for login and when it's start and end
def create_access_token(subject:str |int,expires_delta:timedelta|None=None)->str:
    now=datetime.now(timezone.utc)
    expire_delta=expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire_at= now + expire_delta

    payload={
        "sub":str(subject),
        "iat":now,
        "exp":expire_at,
        "type":"access",
    }
    
    return jwt.encode(payload,JWT_SECRET_KEY,algorithm=JWT_ALGORITHM)

def decode_access_token(token:str)-> dict[str,Any]:
    try:
        payload= jwt.decode(token,JWT_SECRET_KEY,algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cloud not validate credentials",
            headers={"WWW-Authenticate" : "Bearer"},

        )from exc 
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate" :"Bearer"},

        )
    
    return payload