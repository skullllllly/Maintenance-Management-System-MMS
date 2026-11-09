from collections.abc import AsyncIterator

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import  AsyncSession ,async_sessionmaker,create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import  settings

#intilaztion async engine with connection polling optimization
engine=create_async_engine(
    settings.async_database_url,
    echo=False, #set to false in production environment 
    future=True,
    pool_pre_ping=True,
) 

async_session=async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


#async session factory 

AsyncSessonLocal=async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    """Base orm class for all database models."""
    pass 


async def get_db() ->AsyncGenerator[AsyncSession,None]:
    """dependency provider for FastApi route endpoint to yield a database session. """
    async with AsyncSessonLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            