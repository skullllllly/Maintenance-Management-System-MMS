from app.db.session import Base

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import  DateTime,String,func,Integer,Text
from sqlalchemy.orm  import Mapped,mapped_column,relationship

if TYPE_CHECKING:
    from app.models.ticket import MaintenanceTicket

class TicketCategory(Base):

    __tablename__="categories"

    category_id:Mapped[int]=mapped_column(primary_key=True)
    category_name:Mapped[str]=mapped_column(String(100),unique=True,nullable=False,index=True)
    description:Mapped[str|None]=mapped_column(Text,nullable=True)
    default_sla_minutes:Mapped[int]=mapped_column(Integer,nullable=False,default=120,server_default="120")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False,server_default=func.now())

    tickets:Mapped[list["MaintenanceTicket"]]=relationship(
        "MaintenanceTicket", back_populates="category"
    )


