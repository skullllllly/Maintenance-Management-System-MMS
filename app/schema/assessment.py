from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.assessment import AssessmentStatus
from app.schema.user import UserRead


class AssessmentBase(BaseModel):
    ticket_id: int
    technician_id: int
    assigned_by_ai: bool = True
    ai_score_ranking: float | None = Field(default=None, ge=0)
    assignment_status: AssessmentStatus = AssessmentStatus.PENDING


class AssessmentCreate(AssessmentBase):
    """POST — bind a technician to a ticket."""
    pass


class AssessmentUpdate(BaseModel):
    technician_id: int | None = None
    assigned_by_ai: bool | None = None
    ai_score_ranking: float | None = Field(default=None, ge=0)
    assignment_status: AssessmentStatus | None = None
    completed_at: datetime | None = None


class AssessmentRead(AssessmentBase):
    model_config = ConfigDict(from_attributes=True)

    assignment_id: int
    assigned_at: datetime
    completed_at: datetime | None
    technician: UserRead