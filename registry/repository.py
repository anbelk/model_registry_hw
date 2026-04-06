from sqlalchemy import func, select
from sqlalchemy.orm import Session

from registry.models import ModelVersion, RegisteredModel
from registry.schemas import ModelVersionCreate, ModelVersionUpdate, RegisteredModelCreate, RegisteredModelUpdate, Stage


def create_model(session: Session, payload: RegisteredModelCreate) -> RegisteredModel:
    model = RegisteredModel(name=payload.name, description=payload.description, team=payload.team)
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def list_models(session: Session, team: str | None = None, name: str | None = None) -> list[RegisteredModel]:
    query = select(RegisteredModel).order_by(RegisteredModel.created_at.desc())
    if team:
        query = query.where(RegisteredModel.team == team)
    if name:
        query = query.where(RegisteredModel.name.ilike(f"%{name}%"))
    return list(session.scalars(query).all())


def get_model_by_name(session: Session, name: str) -> RegisteredModel | None:
    query = select(RegisteredModel).where(RegisteredModel.name == name)
    return session.scalar(query)


def update_model(session: Session, model: RegisteredModel, payload: RegisteredModelUpdate) -> RegisteredModel:
    data = payload.model_dump(exclude_unset=True)
    for field in ("description", "team"):
        if field in data:
            setattr(model, field, data[field])
    session.commit()
    session.refresh(model)
    return model


def delete_model(session: Session, model: RegisteredModel) -> None:
    session.delete(model)
    session.commit()


def _next_version_number(session: Session, model_id: int) -> int:
    query = select(func.max(ModelVersion.version)).where(ModelVersion.model_id == model_id)
    current = session.scalar(query)
    return (current or 0) + 1


def create_version(session: Session, model: RegisteredModel, payload: ModelVersionCreate) -> ModelVersion:
    version = ModelVersion(
        model_id=model.id,
        version=_next_version_number(session, model.id),
        stage=payload.stage,
        description=payload.description,
        run_id=payload.run_id,
        parameters=payload.parameters,
        metrics=payload.metrics,
        tags=payload.tags,
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def list_versions(session: Session, model: RegisteredModel, stage: Stage | None = None) -> list[ModelVersion]:
    query = select(ModelVersion).where(ModelVersion.model_id == model.id).order_by(ModelVersion.version.desc())
    if stage:
        query = query.where(ModelVersion.stage == stage)
    return list(session.scalars(query).all())


def get_version(session: Session, model: RegisteredModel, version: int) -> ModelVersion | None:
    query = select(ModelVersion).where(ModelVersion.model_id == model.id, ModelVersion.version == version)
    return session.scalar(query)


def update_version(session: Session, version_obj: ModelVersion, payload: ModelVersionUpdate) -> ModelVersion:
    data = payload.model_dump(exclude_unset=True)
    for field in ("description", "run_id", "parameters", "metrics", "tags"):
        if field in data:
            setattr(version_obj, field, data[field])
    session.commit()
    session.refresh(version_obj)
    return version_obj


def set_stage(session: Session, version_obj: ModelVersion, stage: Stage) -> ModelVersion:
    if stage == "production":
        query = select(ModelVersion).where(
            ModelVersion.model_id == version_obj.model_id,
            ModelVersion.stage == "production",
            ModelVersion.version != version_obj.version,
        )
        for old_prod in session.scalars(query).all():
            old_prod.stage = "archived"
    version_obj.stage = stage
    session.commit()
    session.refresh(version_obj)
    return version_obj


def set_artifact_uri(session: Session, version_obj: ModelVersion, artifact_uri: str) -> ModelVersion:
    version_obj.artifact_uri = artifact_uri
    session.commit()
    session.refresh(version_obj)
    return version_obj
