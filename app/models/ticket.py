from app.db.session import Base

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer,String,Text,DateTime,func,CheckConstraint,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship

if TYPE_CHECKING:
    from app.models.category import TicketCategory
    from app.models.user import User
    from app.models.maintenance_log import MaintenanceLog
    from app.models.ticket_status_history import TicketStatusHistory
    from app.models.ticket_image import TicketImage
    from app.models.assessment import Assessment
    from app.models.payment import Payment


class TicketStatus(str,enum.Enum):
    OPEN="OPEN"
    ASSIGNED="ASSIGNED"
    IN_PROGRESS="IN_PROGRESS"
    RESOLVED="RESOLVED"
    CANCELLED="CANCELLED"

class TicketPriority(str, enum.Enum):
    LOW="LOW"
    MEDIUM="MEDIUM"
    HIGH="HIGH"
    #so hard 
    CRITICAL="CRITICAL"


class MaintenanceTicket(Base):
    __tablename__="tickets"
    __table_args__=(
        CheckConstraint(
            "ticket_status IN ('OPEN','ASSIGNED','IN_PROGRESS','RESOLVED','CANCELLED')",
            name="ck_tickets_status",
        ),
        CheckConstraint(
            "priority_level IN ('LOW','MEDIUM','HIGH','CRITICAL')",
            name="ck_tickets_priority"
        )
    )

    ticket_id:Mapped[int]=mapped_column(primary_key=True)
    title:Mapped[str]=mapped_column(String(200),nullable=False)
    description:Mapped[str]=mapped_column(Text,nullable=False)
    category_id:Mapped[int]=mapped_column( ForeignKey("categories.category_id",ondelete="RESTRICT"),nullable=False,index=True)

    ticket_status:Mapped[str]=mapped_column(
        String(20),nullable=False,default=TicketStatus.OPEN.value,
        server_default=TicketStatus.OPEN.value,
        index=True
    )

    priority_level:Mapped[str]=mapped_column(String(10),nullable=False,default=TicketPriority.MEDIUM.value,server_default=TicketPriority.MEDIUM.value)
    reporter_id:Mapped[int]=mapped_column(ForeignKey("users.user_id",ondelete="RESTRICT"),nullable=False,index=True)
    assigned_technician_id:Mapped[int | None ]=mapped_column(ForeignKey("users.user_id",ondelete="SET NULL"),nullable=True,index=True)

    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())

    category:Mapped["TicketCategory"]=relationship(
        "TicketCategory", back_populates="tickets"
    )
    reporter:Mapped["User"]=relationship("User",foreign_keys="[MaintenanceTicket.reporter_id]",back_populates="reported_tickets")
    assigned_technician:Mapped["User| None"]=relationship("User",foreign_keys="[MaintenanceTicket.assigned_technician_id]",back_populates="assigned_tickets")

    status_history:Mapped[list["TicketStatusHistory"]]=relationship("TicketStatusHistory",back_populates="ticket",cascade="all,delete-orphan")
    maintenance_logs:Mapped[list["MaintenanceLog"]]=relationship("MaintenanceLog",back_populates="ticket",cascade="all,delete-orphan")
    images:Mapped[list["TicketImage"]]=relationship("TicketImage",back_populates="ticket",cascade="all,delete-orphan")
    assessment: Mapped["Assessment | None"] = relationship(
    "Assessment",
    back_populates="ticket",
    uselist=False,
    cascade="all, delete-orphan",
    )
    payment: Mapped["Payment | None"] = relationship(
        "Payment",
        back_populates="ticket",
        uselist=False,
    )
    