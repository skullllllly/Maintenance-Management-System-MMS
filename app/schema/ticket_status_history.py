from datetime import datetime
from pydantic import ConfigDict,BaseModel

from app.models.ticket import TicketStatus
from app.schema.user  import UserRead

class StatusHistoryCreate(BaseModel):
    """ bulit by the ticket-update route , not typed by a random client """

    ticket_id:int 
    old_status:TicketStatus|None=None
    new_status:TicketStatus
    changed_by_user_id:int 

class StatusHistoryRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    history_id:int 
    ticket_id:int 
    old_status:TicketStatus|None
    new_status:TicketStatus
    changed_by_user_id:int 
    changed_at:datetime
    changed_by:UserRead

    