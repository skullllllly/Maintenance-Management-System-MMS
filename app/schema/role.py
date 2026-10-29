from datetime import datetime 
from pydantic import BaseModel,ConfigDict,Field

class RoleBase(BaseModel):
    name_role:str =Field(min_length=2,max_length=20)
    description:str |None =None
    is_active:bool =True


class RoleCreate(RoleBase):
    """POST /roles-client does not send id or timestamps."""
    pass

class RoleUpdate(BaseModel):
    """PATCH /roles/{id}- only send fields that change """

    name_role:str |None =Field(default=None,min_length=2,max_length=20)
    description:str|None=None
    is_active:bool|None=None

class RoleRead(RoleBase):
    """responese schema. built from SQLAlchemy role row."""
    model_config=ConfigDict(from_attributes=True)

    id_role:int 
    created_at:datetime
