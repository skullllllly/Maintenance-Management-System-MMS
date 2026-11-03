from contextlib import asynccontextmanager
from fastapi import FastAPI ,Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.minio_client import minio_client

from app.api.auth import router as auth_router, users_router
from app.api.ticket_images import router as ticket_images_router
from app.services.image_processing import initialize_image_processor
from app.services.minio_client import minio_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup events
    await minio_client.verify_bucket_existence()
    await initialize_image_processor()
    yield
    # shutdown events

app = FastAPI(
    title="Maintenance Dispath Backend ",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ticket_images_router)


#أعطاء الصلاحيات @
@app.get("/health",tags=["System Health"]) 
async def health_check(db:AsyncSession=Depends(get_db)):
    """verifies operational state of postgreSQL and minio integrations. """

    db_result=await db.execute(text("SELECT 1"))
    db_status=bool(db_result.scalar())

    return{
        "status":"online",
        "database_connected":db_status,
        "minio_bucket":minio_client.client is not None 
    }