from miniopy_async import Minio
from app.core.config import settings

class MinIOClient:
    def __init__(self) ->None :
        self.client=Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

    async def verify_bucket_existence(self) -> None:
        """ ensures target bucket exists upon service startup ."""
        found=await self.client.bucket_exists(settings.MINIO_BUCKET_NAME)
        if not found:
            await self.client.make_bucket(settings.MINIO_BUCKET_NAME)


minio_client=MinIOClient()
