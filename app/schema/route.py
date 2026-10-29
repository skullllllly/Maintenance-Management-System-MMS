from datetime import datetime
from pydantic import BaseModel,ConfigDict,Field


class RouteLogBase(BaseModel):
    assignment_id:int 
    origin_latitude:float=Field(...,ge=-90,le=90)
    origin_longtude:float=Field(...,ge=-180,le=180)
    destination_latitude:float=Field(...,ge=-90,le=90)
    destination_longtude:float=Field(...,ge=-180,le=180)
    estimated_distance_km:float=Field(...,ge=0)
    estimated_distance_minutes:int=Field(...,ge=0)
    actual_duration_minutes:int |None =Field(default=None,ge=0)

class RouteLogCreate(RouteLogBase):
    pass

class RouteLogRead(RouteLogBase):
    model_config=ConfigDict(from_attributes=True)

    route_id:int 
    created_at:datetime