from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import Text,Numeric,DateTime,CheckConstraint,ForeignKey,func
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.ticket import MaintenanceTicket
    from app.models.user import User

class MaintenanceLog(Base):

    __tablename__="maintenance_logs"
    __table_args__=(
        CheckConstraint( "hours_spent >=0",name="ck_logs_hours_spent"),
    )

    log_id:Mapped[int]=mapped_column(primary_key=True)

    ticket_id:Mapped[int]=mapped_column(ForeignKey("tickets.ticket_id",ondelete="CASCADE"),nullable=False,index=True)
    technician_id:Mapped[int]=mapped_column(ForeignKey("users.user_id",ondelete="RESTRICT"),nullable=False,index=True)

    action_taken:Mapped[str]=mapped_column(Text,nullable=False)
    hours_spent:Mapped[Decimal]=mapped_column(Numeric(4,2),nullable=False)
    logged_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())

    ticket:Mapped["MaintenanceTicket"]=relationship(
        "MaintenanceTicket",back_populates="maintenance_logs"
    )
    technician:Mapped["User"]=relationship("User",back_populates="maintenance_logs")

