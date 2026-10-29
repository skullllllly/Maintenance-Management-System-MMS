from datetime import datetime
from pydantic  import BaseModel,ConfigDict,Field

class CategoryBase(BaseModel):
    category_name:str=Field(min_length=2,max_length=100)
    description:str |None =None
    #gt =greater than 0
    default_sla_minutes:int =Field(default=120,gt=0)


class CategoryCreate(CategoryBase):
    #inhartins
    """ post / categories """ 
    pass 

class CategoryUpdate(BaseModel):
    category_name:str |None =Field(default=None,min_length=2,max_length=100)
    description:str |None =None
    default_sla_minutes: int| None=Field(default=None,gt=0)


class CategoryRead(CategoryBase):
    model_config=ConfigDict(from_attributes=True)

    category_id:int 
    created_at:datetime