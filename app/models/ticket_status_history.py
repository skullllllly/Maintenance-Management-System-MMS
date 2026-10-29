from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String,ForeignKey,func,DateTime,CheckConstraint
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.ticket import MaintenanceTicket


class TicketStatusHistory(Base):
    __tablename__="ticket_status_history"
    __table_args__=(

        CheckConstraint(
            "(old_status IS NULL OR old_status IN " 
            "('OPEN','ASSIGNED','IN_PROGRESS','RESOLVED','CANCELLED'))",
            name="ck_history_old_status",
        ),
        CheckConstraint(
            "new_status IN ('OPEN','ASSIGNED','IN_PROGRESS','RESOLVED','CANCELLED')",
            name="ck_history_new_status",
        )
    )

    history_id:Mapped[int]=mapped_column(primary_key=True)
    ticket_id:Mapped[int]=mapped_column( 
        ForeignKey("tickets.ticket_id",ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    old_status:Mapped[str|None]=mapped_column(String(100),nullable=True)
    new_status:Mapped[str ]=mapped_column(String(100),nullable=False)

    changed_by_user_id:Mapped[int]=mapped_column(ForeignKey("users.user_id",ondelete="RESTRICT"),nullable=False,index=True)
    changed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())

    ticket:Mapped["MaintenanceTicket"]=relationship("MaintenanceTicket",back_populates="status_history")
    changed_by:Mapped["User"]=relationship("User",back_populates="status_changes")


