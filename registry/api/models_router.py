from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from registry.database import get_db
from registry.repository import create_model, delete_model, get_model_by_name, list_models, update_model
from registry.schemas import RegisteredModelCreate, RegisteredModelResponse, RegisteredModelUpdate

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.post("", response_model=RegisteredModelResponse, status_code=status.HTTP_201_CREATED)
def create_registered_model(payload: RegisteredModelCreate, db: Session = Depends(get_db)) -> RegisteredModelResponse:
    try:
        model = create_model(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model with this name already exists")
    return RegisteredModelResponse.model_validate(model)


@router.get("", response_model=list[RegisteredModelResponse])
def get_models(team: str | None = None, name: str | None = None, db: Session = Depends(get_db)) -> list[RegisteredModelResponse]:
    items = list_models(db, team=team, name=name)
    return [RegisteredModelResponse.model_validate(item) for item in items]


@router.get("/{name}", response_model=RegisteredModelResponse)
def get_model(name: str, db: Session = Depends(get_db)) -> RegisteredModelResponse:
    model = get_model_by_name(db, name)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return RegisteredModelResponse.model_validate(model)


@router.patch("/{name}", response_model=RegisteredModelResponse)
def patch_model(name: str, payload: RegisteredModelUpdate, db: Session = Depends(get_db)) -> RegisteredModelResponse:
    model = get_model_by_name(db, name)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    updated = update_model(db, model, payload)
    return RegisteredModelResponse.model_validate(updated)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def remove_model(name: str, db: Session = Depends(get_db)) -> None:
    model = get_model_by_name(db, name)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    delete_model(db, model)
