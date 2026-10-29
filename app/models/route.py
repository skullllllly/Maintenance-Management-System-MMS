from datetime import datetime
from sqlalchemy import DateTime,Double,Integer,ForeignKey,func
from sqlalchemy.orm import Mapped,mapped_column,relationship

from typing import TYPE_CHECKING
from app.db.session import Base

class RoutLog(Base):
    __tablename__="route_logs"

    route_id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    assignment_id:Mapped[int]=mapped_column(Integer,ForeignKey("assignments.assignment_id",ondelete="RESTRICT"),nullable=False,index=True)
    origin_latitude:Mapped[float]=mapped_column(Double,nullable=False)
    origin_longtude:Mapped[float]=mapped_column(Double,nullable=False)
    destination_latitude:Mapped[float]=mapped_column(Double,nullable=False)
    destination_longtude:Mapped[float]=mapped_column(Double,nullable=False)
    estimated_distance_km:Mapped[float]=mapped_column(Double,nullable=False)
    estimated_distance_minutes:Mapped[int]=mapped_column(Integer,nullable=False) 
    actual_duration_minutes:Mapped[int|None]=mapped_column(Integer,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())

    assessment:Mapped["Assessment"]=relationship("Assessment",back_populates="route")