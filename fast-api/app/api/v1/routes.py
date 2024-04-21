from fastapi import APIRouter

from .endpoints import router as create_user


router = APIRouter()

router.include_router(create_user)
