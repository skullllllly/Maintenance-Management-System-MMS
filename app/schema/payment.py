from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentMethod, PaymentStatus


class PaymentBase(BaseModel):
    ticket_id: int
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    payment_method: PaymentMethod
    transaction_reference: str | None = Field(default=None, max_length=100)


class PaymentCreate(PaymentBase):
    """POST — open a charge. Status starts PENDING; paid_at stays null."""
    pass


class PaymentUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    payment_method: PaymentMethod | None = None
    payment_status: PaymentStatus | None = None
    transaction_reference: str | None = Field(default=None, max_length=100)
    paid_at: datetime | None = None


class PaymentRead(PaymentBase):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int
    payment_status: PaymentStatus
    paid_at: datetime | None