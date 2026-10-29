from datetime import datetime
from pydantic import ConfigDict,BaseModel,Field,HttpUrl

class TicketImageCreate(BaseModel):
    """built after a successful MinIO put-object -not a public  JSON  body"""

    ticket_id:int 
    minio_object_name:str=Field(min_length=1,max_length=500)
    file_url:str=Field(min_length=1)

class TicketImageRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    image_id:int 
    ticket_id:int 
    file_url:str
    uploaded_at:datetime
    minio_object_name:str