from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from registry.database import Base

JSONType = JSON().with_variant(JSONB, "postgresql")


class RegisteredModel(Base):
    __tablename__ = "registered_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    team: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    versions: Mapped[list["ModelVersion"]] = relationship(
        "ModelVersion",
        back_populates="model",
        cascade="all, delete-orphan",
        order_by="ModelVersion.version",
    )


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("model_id", "version", name="uq_model_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("registered_models.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="none", server_default="none", index=True)
    parameters: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    metrics: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    tags: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    artifact_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    model: Mapped[RegisteredModel] = relationship("RegisteredModel", back_populates="versions")
