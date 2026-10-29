from datetime import datetime
from pydantic import BaseModel,ConfigDict,Field

from app.models.ticket import TicketPriority,TicketStatus
from app.schema.category import CategoryRead
from app.schema.user import UserRead

class TicketBase(BaseModel):
    title:str =Field(min_length=2,max_length=200)
    description:str=Field(min_length=3)
    category_id:int 
    priority_level:TicketPriority =TicketPriority.MEDIUM

class TicketCreate(TicketBase):
    """post / tickets - new job starts OPEN and unassigned """

    reporter_id:int 

class TicketUpdate(BaseModel):
    title:str|None =Field(default=None,min_length=2,max_length=200)
    description:str |None=Field(default=None,min_length=3)
    category_id:int |None=None
    ticket_status:TicketStatus|None=None
    priority_level:TicketPriority|None=None
    assigned_technician_id:int |None =None 


class TicketRead(BaseModel):
    """response hash never appears ,user come through UserRead"""
    model_config=ConfigDict(from_attributes=True)

    ticket_id:int 
    reporter_id:int 
    title:str
    description:str
    category_id:int 
    ticket_status:TicketStatus
    priority_level:TicketPriority
    assigned_technician_id:int |None 
    created_at:datetime
    updated_at:datetime
    category:CategoryRead
    reporter:UserRead
    assigned_technician:UserRead|None
