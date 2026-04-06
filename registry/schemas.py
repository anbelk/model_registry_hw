from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Stage = Literal["none", "staging", "production", "archived"]


class RegisteredModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    team: str | None = Field(default=None, max_length=255)


class RegisteredModelUpdate(BaseModel):
    description: str | None = None
    team: str | None = Field(default=None, max_length=255)


class RegisteredModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None
    team: str | None
    created_at: datetime
    updated_at: datetime


class ModelVersionCreate(BaseModel):
    description: str | None = None
    run_id: str | None = Field(default=None, max_length=255)
    parameters: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    tags: dict[str, Any] = Field(default_factory=dict)
    stage: Stage = "none"


class ModelVersionUpdate(BaseModel):
    description: str | None = None
    run_id: str | None = Field(default=None, max_length=255)
    parameters: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    tags: dict[str, Any] | None = None


class StageUpdate(BaseModel):
    stage: Stage


class ModelVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version: int
    stage: Stage
    description: str | None
    run_id: str | None
    parameters: dict[str, Any]
    metrics: dict[str, Any]
    tags: dict[str, Any]
    artifact_uri: str | None
    created_at: datetime
    updated_at: datetime
