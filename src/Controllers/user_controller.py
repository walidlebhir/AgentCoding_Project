from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.dependencies.auth_dependency import get_current_user
from src.models.user import User

router = APIRouter(tags=["users"])


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
