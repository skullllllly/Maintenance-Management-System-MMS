import uuid
from datetime import datetime 

from sqlalchemy import CheckConstraint,DateTime,String,UniqueConstraint,func
from sqlalchemy.dialects.postgresql import JSONB,UUID
from sqlalchemy.orm import Mapped,mapped_column

from app.db.session import Base
from app.ml_contract import DEFECT_LABELS,FEATURE_PIPELINE_VERSION,FEATURE_DIMENSION

_LABEL_SQL= " , ".join(f"'{label}'" for label in DEFECT_LABELS)

class DefectTrainingSample(Base):
    __tablename__="defect_training_samples"
    __table_args__=(
        UniqueConstraint(
            "dataset_version",
            "relative_path",
            name="uq_defect_training_dataset_path"
        ),
        CheckConstraint(
            f"label IN ({_LABEL_SQL})",
            name="ck_defect_training_label",
        ),
        CheckConstraint(
            "split IN ('train','test')",
            name="ck_defect_training_split"
        ),
        CheckConstraint(
            f"json_array_length(cnn_features)= {FEATURE_DIMENSION}",
            name="ck_defect_training_feature_dimension"
        ),
    )

    image_id:Mapped[uuid.UUID]=mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    dataset_version:Mapped[str]=mapped_column(String(100),nullable=False)
    relative_path:Mapped[str]=mapped_column(String(1000),nullable=False)
    label:Mapped[str]=mapped_column(String(100),nullable=False)
    split:Mapped[str]=mapped_column(String(8),nullable=False)
    feature_pipeline_version:Mapped[str]=mapped_column(String(100),nullable=False)
    cnn_features:Mapped[list[float]]=mapped_column(JSONB,nullable=False)
    created_at:Mapped[datetime]=mapped_column(
    DateTime(timezone=True),
    nullable=False,
    server_default=func.now())