from datetime import datetime 
from pydantic import BaseModel ,ConfigDict,EmailStr,Field 
from app.schema.role import RoleRead

class UserBase(BaseModel):
    full_name: str =Field(min_length=2,max_length=100)
    email:EmailStr
    phone_number:str =Field(min_length=8,max_length=20)
    id_role:int 
    is_active:bool=True

class UserCreate(UserBase):
    password:str =Field(min_length=8,max_length=200)


class UserLogin(BaseModel):
    email:EmailStr
    password:str = Field(...,min_length=8,max_length=200)


class UserUpdate(BaseModel):
    full_name:str|None =Field(default=None ,min_length=2,max_length=100)
    email:EmailStr |None =None
    phone_number:str |None =Field(default=None,min_length=2,max_length=20)
    id_role:int |None=None 
    is_active:bool |None =None 
    password:str|None=Field(default=None,min_length=8,max_length=200)

class UserRead(UserBase):
    """safe response :hash is never included """
    model_config=ConfigDict(from_attributes=True)

    user_id:int
    created_at:datetime
    updated_at:datetime
    role:RoleRead