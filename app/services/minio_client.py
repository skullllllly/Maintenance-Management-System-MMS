import asyncio
import io
import uuid
from datetime import timedelta

from miniopy_async import Minio
from miniopy_async.commonconfig import CopySource
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
        if not await self.client.bucket_exists(settings.MINIO_BUCKET_NAME):
            await self.client.make_bucket(settings.MINIO_BUCKET_NAME)

    async def upload_ticket_image(
        self,
        ticket_id,
        image_bytes:bytes,
        content_type:str
    ) -> tuple[str, str]:
        object_name = f"tickets/{ticket_id}/{uuid.uuid4().hex}"

        await self.client.put_object(
            settings.MINIO_BUCKET_NAME,
            object_name,
            io.BytesIO(image_bytes),
            length=len(image_bytes),
            content_type=content_type,
        )

        file_url = await self.client.get_presigned_url(
            "GET",
            settings.MINIO_BUCKET_NAME,
            object_name,
            expires=timedelta(days=7),
        )
        return object_name, file_url

    async def delete_object(self, object_name: str) -> None:
        await self.client.remove_object(
            settings.MINIO_BUCKET_NAME,
            object_name,
        )

minio_client=MinIOClient()
