from fastapi import APIRouter
from app.api.v1.endpoints import auth, analytics, channels, videos

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(channels.router, prefix="/channels", tags=["Channels"])
api_router.include_router(videos.router, prefix="/videos", tags=["Videos"])
