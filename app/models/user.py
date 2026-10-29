from app.db.session import Base

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean,DateTime,String,ForeignKey,func
from sqlalchemy.orm import Mapped,mapped_column,relationship

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.ticket import MaintenanceTicket
    from app.models.maintenance_log import MaintenanceLog
    from app.models.ticket_status_history import TicketStatusHistory
    from app.models.assessment import Assessment
   

class User(Base):
    """people who log in :client,technicians,dispatchers,admins."""

    __tablename__="users"

    user_id:Mapped[int]=mapped_column(primary_key=True)
    full_name:Mapped[str]=mapped_column(String(100),nullable=False)
    email:Mapped[str]=mapped_column(String(150),unique=True,nullable=False,index=True)
    password_hash:Mapped[str]=mapped_column(String(255),nullable=False)
    phone_number:Mapped[str]=mapped_column(String(20),unique=True,nullable=False)
    id_role:Mapped[int]=mapped_column( ForeignKey("roles.id_role",ondelete="RESTRICT") , nullable=False,index=True)
    is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default="true")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())

    role:Mapped["Role"]=relationship("Role",back_populates="users",)
    reported_tickets:Mapped[list["MaintenanceTicket"]]=relationship(
        "MaintenanceTicket",foreign_keys="[MaintenanceTicket.reporter_id]",back_populates="reporter"
    )
    assigned_tickets:Mapped[list["MaintenanceTicket"]]=relationship("MaintenanceTicket",foreign_keys="[MaintenanceTicket.assigned_technician_id]",back_populates="assigned_technician")

    status_changes:Mapped[list["TicketStatusHistory"]]=relationship("TicketStatusHistory",back_populates="changed_by")
    maintenance_logs:Mapped[list["MaintenanceLog"]]=relationship("MaintenanceLog",back_populates="technician")
    assessments: Mapped[list["Assessment"]] = relationship(
        "Assessment",
        back_populates="technician",
    )