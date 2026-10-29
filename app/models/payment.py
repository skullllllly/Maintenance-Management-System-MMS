import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint,DateTime,String,Numeric,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.ticket import MaintenanceTicket


class PaymentMethod(str,enum.Enum):
    CASH="CASH"
    CREDIT_CARD="CREDIT_CARD"
    E_WALLET="E_WALLET"
    BANK_TRANSFER="BANK_TRANSFER"

class PaymentStatus(str,enum.Enum):
    PENDING="PENDING"
    COMPLETED="COMPLETED"
    FAILED="FAILED"
    REFUNDED="REFUNDED"

class Payment(Base):
    __tablename__="payments"
    __table_args__=(

        CheckConstraint("amount > 0",name="ck_payments_amount_positive"),
        CheckConstraint("payment_method IN ('CASH','CREDIT_CARD','E_WALLET','BANK_TRANSFER')",
        name="ck_payments_method"),

        CheckConstraint("payment_status IN ('PENDING','COMPLETED','FAILED','REFUNDED')",
        name="ck_payments_status"),
        )

    payment_id:Mapped[int]=mapped_column(primary_key=True)
    ticket_id:Mapped[int]=mapped_column(ForeignKey("tickets.ticket_id",ondelete="RESTRICT"),nullable=False,unique=True,index=True)
    amount:Mapped[Decimal]=mapped_column(Numeric(10,2),nullable=False)
    payment_method:Mapped[str]=mapped_column(String(20),nullable=False)
    payment_status:Mapped[str]=mapped_column(String(20),nullable=False,default=PaymentStatus.PENDING.value,server_default=PaymentStatus.PENDING.value,index=True)
    transaction_reference:Mapped[str|None]=mapped_column(String(100),nullable=True)

    paid_at:Mapped[datetime | None]=mapped_column(DateTime(timezone=True),nullable=True,index=True)

    ticket:Mapped["MaintenanceTicket"]=relationship("MaintenanceTicket",back_populates="payment")