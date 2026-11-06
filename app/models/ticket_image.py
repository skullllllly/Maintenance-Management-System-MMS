from datetime import datetime
from typing import TYPE_CHECKING

from app.db.session import Base

from sqlalchemy import Text,ForeignKey,String,DateTime,func,Float,Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped,mapped_column,relationship

if TYPE_CHECKING:
    from app.models.ticket import MaintenanceTicket

class TicketImage(Base):
    __tablename__="image_logs"

    image_id:Mapped[int]=mapped_column(primary_key=True)
    ticket_id:Mapped[int]=mapped_column(ForeignKey("tickets.ticket_id",ondelete="CASCADE"),nullable=False,index=True)

    file_url:Mapped[str]=mapped_column(Text,nullable=False)
    minio_object_name:Mapped[str]=mapped_column(String(500),unique=True,nullable=False,index=True)

    blur_variance:Mapped[float| None]=mapped_column(Float,nullable=True)
    is_blurry:Mapped[bool|None]=mapped_column(Boolean,nullable=True)
    cnn_features:Mapped[list[float] | None]=mapped_column(
        JSONB,
        nullable=True
    )

    defect_label:Mapped[str |None ]=mapped_column(String(100),nullable=True)
    defect_label_source:Mapped[str| None]=mapped_column(String(50),nullable=True)
    defect_labeled_at:Mapped[datetime |None]=mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now()
        )

    processing_status:Mapped[str]=mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
    )

    uploaded_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())

    ticket:Mapped["MaintenanceTicket"]=relationship("MaintenanceTicket",back_populates="images")