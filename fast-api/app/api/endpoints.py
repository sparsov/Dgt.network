from fastapi import APIRouter

from app.core.models import User, UserCreate
from app.core.security import get_password_hash

router = APIRouter()


@router.post("/users", response_model=User)
async def create_user(user: UserCreate):
    # Логика для создания нового пользователя
    # В этом примере мы просто возвращаем переданные данные пользователя
    hashed_password = get_password_hash(user.password)
    created_user = User(id=1, username=user.username)
    return created_user
