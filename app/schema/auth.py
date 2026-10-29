from pydantic import BaseModel,ConfigDict

class TokenData(BaseModel):
    sub:str|None=None

    model_config=ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token:str
    token_type:str= "bearer"

    model_config=ConfigDict(from_attributes=True)