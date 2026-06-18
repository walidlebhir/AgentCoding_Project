from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.dependencies.auth_dependency import get_current_user
from src.models.user import User

router = APIRouter(prefix="/agent", tags=["agent"])


class GenerateRequest(BaseModel):
    project_id: str
    prompt: str


class GenerateResponse(BaseModel):
    success: bool
    message: str


@router.post("/generate", response_model=GenerateResponse)
def generate(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
):
    return GenerateResponse(
        success=True,
        message=f"AI generation for project {body.project_id} will be implemented soon",
    )
