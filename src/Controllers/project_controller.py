from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.Config.database import get_db
from src.dependencies.auth_dependency import get_current_user
from src.models.user import User
from src.Services.project_service import (
    create_project,
    delete_project,
    get_project,
    get_user_projects,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    language: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    language: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    language: str | None
    prompt: str | None
    steps: str | None
    folder_name: str | None
    download_url: str | None
    provider: str | None
    model: str | None
    generation_time: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=ProjectResponse, status_code=201)
def create(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_project(
        db,
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        language=body.language,
    )


@router.get("", response_model=list[ProjectResponse])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_projects(db, user_id=current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_one(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_project(db, project_id=project_id, user_id=current_user.id)


@router.put("/{project_id}", response_model=ProjectResponse)
def update(
    project_id: str,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_project(
        db,
        project_id=project_id,
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        language=body.language,
    )


@router.delete("/{project_id}", status_code=204)
def delete(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_project(db, project_id=project_id, user_id=current_user.id)
