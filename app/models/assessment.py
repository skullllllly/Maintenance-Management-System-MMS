import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    func
)

from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.ticket import MaintenanceTicket
    from app.models.user import User


class AssessmentStatus(str,enum.Enum):
    PENDING="PENDING"
    ACCEPTED="ACCEPTED"
    COMPLETED="COMPLETED"
    REJECTED="REJECTED"
   


class Assessment(Base):
    __tablename__="assignments"
    __table_args__=(
        CheckConstraint(
            "assignment_status IN "
            "('PENDING','ACCEPTED','COMPLETED','REJECTED')",
            name="CK_assignment_status",
        ),
    )

    assignment_id:Mapped[int]=mapped_column(primary_key=True)
    ticket_id:Mapped[int]=mapped_column(ForeignKey("tickets.ticket_id",ondelete="CASCADE"),nullable=False,unique=True,index=True,)
    technician_id:Mapped[int]=mapped_column(ForeignKey("users.user_id",ondelete="RESTRICT"),nullable=False,index=True)
    assigned_by_ai:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default="true")
    ai_score_ranking:Mapped[float|None]=mapped_column(Float,nullable=True)

    assignment_status:Mapped[str]=mapped_column(String(20),nullable=False,default=AssessmentStatus.PENDING.value,server_default=AssessmentStatus.PENDING.value,index=True)

    assigned_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),index=True)
    completed_at:Mapped[datetime |None]=mapped_column(DateTime(timezone=True),nullable=True)

    ticket:Mapped["MaintenanceTicket"]=relationship("MaintenanceTicket",back_populates="assessment")
    technician:Mapped["User"]=relationship("User",back_populates="assessments")
    route:Mapped["RoutLog"]=relationship("RoutLog",back_populates="assessment")
