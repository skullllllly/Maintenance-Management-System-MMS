from datetime import datetime
from typing import TYPE_CHECKING

from app.db.session import Base

from sqlalchemy import Text,ForeignKey,String,DateTime,func
from sqlalchemy.orm import Mapped,mapped_column,relationship

if TYPE_CHECKING:
    from app.models.ticket import MaintenanceTicket

class TicketImage(Base):
    __tablename__="image_logs"

    image_id:Mapped[int]=mapped_column(primary_key=True)
    ticket_id:Mapped[int]=mapped_column(ForeignKey("tickets.ticket_id",ondelete="CASCADE"),nullable=False,index=True)

    file_url:Mapped[str]=mapped_column(Text,nullable=False)
    minio_object_name:Mapped[str]=mapped_column(String(500),unique=True,nullable=False,index=True)

    uploaded_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())

    ticket:Mapped["MaintenanceTicket"]=relationship("MaintenanceTicket",back_populates="images")