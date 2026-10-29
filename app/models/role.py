from app.db.session import Base

from datetime import datetime
from typing import TYPE_CHECKING 
from sqlalchemy import Boolean ,DateTime, String ,Text ,func
from sqlalchemy.orm import Mapped,mapped_column,relationship

if TYPE_CHECKING:
    from app.models.user import User


class Role(Base):
    """from postgralSQl  conect the tables into project """

    __tablename__="roles"

    id_role:Mapped[int]=mapped_column(primary_key=True)
    name_role:Mapped[str]=mapped_column(String(20),unique=True,nullable=False,index=True)
    description:Mapped[str | None ]=mapped_column(Text,nullable=True)
    is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default="true")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),)

    users:Mapped[list["User"]]=relationship("User",back_populates="role")





