from datetime import datetime 
from decimal import Decimal

from pydantic import ConfigDict,BaseModel,Field

from app.schema.user import UserRead

class MaintenanceLogCreate(BaseModel):
    
    ticket_id:int 
    technician_id:int 
    action_taken:str=Field(min_length=3)
    hours_spent:Decimal=Field(gt=0,max_digits=4,decimal_places=2)

class MaintenanceLogRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)

    log_id:int 
    ticket_id:int 
    technician_id:int 
    action_taken:str
    hours_spent:Decimal
    logged_at:datetime
    technician:UserRead

