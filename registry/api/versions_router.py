import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from registry.config import get_settings
from registry.database import get_db
from registry.repository import (
    create_version,
    get_model_by_name,
    get_version,
    list_versions,
    set_artifact_uri,
    set_stage,
    update_version,
)
from registry.schemas import ModelVersionCreate, ModelVersionResponse, ModelVersionUpdate, Stage, StageUpdate
from registry.storage import Storage, StorageUnavailableError

router = APIRouter(prefix="/api/v1/models/{name}/versions", tags=["versions"])


def get_storage() -> Storage:
    return Storage()


def _sanitize_filename(file_name: str | None) -> str:
    cleaned = os.path.basename(file_name or "artifact.bin")
    if not cleaned:
        return "artifact.bin"
    return cleaned.replace("/", "_").replace("\\", "_")


@router.post("", response_model=ModelVersionResponse, status_code=status.HTTP_201_CREATED)
def create_model_version(
    name: str,
    payload: ModelVersionCreate,
    db: Session = Depends(get_db),
) -> ModelVersionResponse:
    model = get_model_by_name(db, name)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    try:
        version = create_version(db, model, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Integrity constraint violation")
    return ModelVersionResponse.model_validate(version)


@router.get("", response_model=list[ModelVersionResponse])
def get_model_versions(name: str, stage: Stage | None = None, db: Session = Depends(get_db)) -> list[ModelVersionResponse]:
    model = get_model_by_name(db, name)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    versions = list_versions(db, model, stage=stage)
    return [ModelVersionResponse.model_validate(item) for item in versions]


@router.get("/{version}", response_model=ModelVersionResponse)
def get_model_version(name: str, version: int, db: Session = Depends(get_db)) -> ModelVersionResponse:
    model = get_model_by_name(db, name)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    version_obj = get_version(db, model, version)
    if version_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return ModelVersionResponse.model_validate(version_obj)


@router.patch("/{version}", response_model=ModelVersionResponse)
def patch_model_version(
    name: str,
    version: int,
    payload: ModelVersionUpdate,
    db: Session = Depends(get_db),
) -> ModelVersionResponse:
    model = get_model_by_name(db, name)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    version_obj = get_version(db, model, version)
    if version_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    updated = update_version(db, version_obj, payload)
    return ModelVersionResponse.model_validate(updated)


@router.put("/{version}/stage", response_model=ModelVersionResponse)
def update_model_stage(
    name: str,
    version: int,
    payload: StageUpdate,
    db: Session = Depends(get_db),
) -> ModelVersionResponse:
    model = get_model_by_name(db, name)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    version_obj = get_version(db, model, version)
    if version_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    updated = set_stage(db, version_obj, payload.stage)
    return ModelVersionResponse.model_validate(updated)


@router.post("/{version}/artifacts", response_model=ModelVersionResponse)
async def upload_artifact(
    name: str,
    version: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: Storage = Depends(get_storage),
) -> ModelVersionResponse:
    model = get_model_by_name(db, name)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    version_obj = get_version(db, model, version)
    if version_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    payload = await file.read()
    if len(payload) > get_settings().artifact_max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Artifact too large")
    safe_name = _sanitize_filename(file.filename)
    object_name = f"{name}/v{version}/{safe_name}"
    try:
        artifact_uri = storage.upload_bytes(object_name, payload, content_type=file.content_type or "application/octet-stream")
    except StorageUnavailableError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Storage unavailable")
    updated = set_artifact_uri(db, version_obj, artifact_uri)
    return ModelVersionResponse.model_validate(updated)


@router.get("/{version}/artifacts/{filename}")
def download_artifact(
    name: str,
    version: int,
    filename: str,
    db: Session = Depends(get_db),
    storage: Storage = Depends(get_storage),
) -> RedirectResponse:
    model = get_model_by_name(db, name)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    version_obj = get_version(db, model, version)
    if version_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    safe_name = _sanitize_filename(filename)
    object_name = f"{name}/v{version}/{safe_name}"
    try:
        exists = storage.object_exists(object_name)
    except StorageUnavailableError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Storage unavailable")
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    try:
        presigned_url = storage.presigned_get_url(object_name)
    except StorageUnavailableError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Storage unavailable")
    return RedirectResponse(url=presigned_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
