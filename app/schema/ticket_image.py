from datetime import datetime
from typing import Literal
from pydantic import ConfigDict,BaseModel,Field,HttpUrl

class TicketImageCreate(BaseModel):
    """built after a successful MinIO put-object -not a public  JSON  body"""

    ticket_id:int 
    minio_object_name:str=Field(min_length=1,max_length=500)
    file_url:str=Field(min_length=1)
    blur_variance:float=Field(ge=0)
    is_blurry:bool
    cnn_features:list[float]=Field(min_length=1)
    processing_status:Literal["PENDING","COMPLETED","FAILED"]

class TicketImageRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    image_id:int 
    ticket_id:int 
    file_url:str
    minio_object_name:str
    blur_variance:float |None
    is_blurry:bool| None
    cnn_features:list[float]| None
    processing_status: str
    uploaded_at:datetime
    