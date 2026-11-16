from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.urls import router as urls_router
from app.api.v1.analytics import router as analytics_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(urls_router)
api_v1_router.include_router(analytics_router)

__all__ = ["api_v1_router"]
