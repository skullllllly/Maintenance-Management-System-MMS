from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter,Depends,File,Form,HTTPException,UploadFile,status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.curd.ticket_image import create
from app.db.session import get_db
from app.schema.ticket_image import TicketImageCreate,TicketImageRead
from app.services.image_processing import (
    ImageProcessingError,
    analyze_image,
    read_limited_upload,
)
from app.services.minio_client import minio_client

from app.curd.ticket_image import get_by_id
from app.services.defect_classifier import(
    DefectClassifierError,
    defect_classifier
)

import logging
import asyncio

logger=logging.getLogger(__name__)

router=APIRouter(prefix="/ticket-image", tags=["Ticket Image"])

ALLOWED_IMAGE_TYPES={
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/jpg",
}

@router.post(
    "",
    response_model=TicketImageRead,
    status_code=status.HTTP_200_OK,
)
async def ingest_ticket_image(
    ticket_id:Annotated[int,Form(gt=0)],
    file:Annotated[UploadFile,File(...)],
    db:AsyncSession=Depends(get_db),

)->TicketImageRead:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type : {file.content_type}",
            )
    
    try:
        image_bytes=await read_limited_upload(file)
        processed=await analyze_image(image_bytes)

    except ImageProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )from exc
    finally:
        await file.close()

    object_name= ""
    try:
        object_name,file_url=await minio_client.upload_ticket_image(
            ticket_id=ticket_id,
            image_bytes=image_bytes,
            content_type=file.content_type,
        )
        payload=TicketImageCreate(
            ticket_id=ticket_id,
            minio_object_name=object_name,
            file_url=file_url,
            blur_variance=processed.blur_variance,
            is_blurry=processed.is_blurry,
            cnn_features=processed.cnn_features,
            processing_status="COMPLETED"
        )
        image= await create(db,payload)
        await db.commit()
        await db.refresh(image)
        return TicketImageRead.model_validate(image)

    except ValueError as exc :
        await db.rollback()

        if object_name:
            await minio_client.delete_object(object_name)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )from exc

    except SQLAlchemyError as exc:
        await db.rollback()

        if object_name:
            await minio_client.delete_object(object_name)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image metadata could not be persisted",
        )from exc


@router.get(
    "/{image_id}/defect-classification",
    response_model=DefectPrediction,
)
async def classify_ticket_image(
    image_id:int,
    db:AsyncSession=Depends(get_db),
) -> DefectPrediction
    image=await get_by_id(db,image_id)

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket image not found ",
        )

    if image.processing_status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Image processing is not copmlete"
        )

    if image.cnn_features is None :
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No CNN feature  are available for this image "
        )

    try :
        return await asyncio.to_thread(
            defect_classifier.predict,
            image_id=image.image_id,
            cnn_features=image.cnn_features
        )

    except DefectClassifierError as exc :
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )from exc
        
    except Exception:
        logger.exception(
            "Unexpected classification failure for image_id=%s",
            image.image_id
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= "Defect classification failed",
        )