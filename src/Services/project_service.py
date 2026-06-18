from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.project import Project


def create_project(
    db: Session,
    user_id: str,
    name: str,
    description: str | None = None,
    language: str | None = None,
    prompt: str | None = None,
    folder_name: str | None = None,
    download_url: str | None = None,
    steps: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    generation_time: float | None = None,
) -> Project:
    project = Project(
        user_id=user_id,
        name=name,
        description=description,
        language=language,
        prompt=prompt,
        folder_name=folder_name,
        download_url=download_url,
        steps=steps,
        provider=provider,
        model=model,
        generation_time=generation_time,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_user_projects(db: Session, user_id: str) -> list[Project]:
    """Get all projects for a user, ordered by most recent first."""
    return (
        db.query(Project)
        .filter(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .all()
    )


def _get_project_or_404(db: Session, project_id: str) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _ensure_owner(project: Project, user_id: str) -> None:
    if project.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your project")


def get_project(db: Session, project_id: str, user_id: str) -> Project:
    project = _get_project_or_404(db, project_id)
    _ensure_owner(project, user_id)
    return project


def update_project(
    db: Session,
    project_id: str,
    user_id: str,
    name: str | None = None,
    description: str | None = None,
    language: str | None = None,
) -> Project:
    project = _get_project_or_404(db, project_id)
    _ensure_owner(project, user_id)

    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if language is not None:
        project.language = language

    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: str, user_id: str) -> None:
    project = _get_project_or_404(db, project_id)
    _ensure_owner(project, user_id)
    db.delete(project)
    db.commit()
