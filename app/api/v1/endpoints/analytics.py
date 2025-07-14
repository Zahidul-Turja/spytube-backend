from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict
from app.dependencies import get_current_user
from app.services.auth_service import auth_service
import httpx
from datetime import datetime, timedelta

from app.utils.user_storage import user_storage

router = APIRouter()


YOUTUBE_DATA_URL = "https://www.googleapis.com/youtube/v3/channels"
YOUTUBE_ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"


@router.get("/dashboard")
async def get_dashboard_analytics(current_user: Dict = Depends(get_current_user)):
    user_tokens = user_storage.get_user_tokens(current_user["id"])
    if not user_tokens:
        raise HTTPException(status_code=401, detail="Google tokens not found")

    access_token = user_tokens.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Google access token missing")

    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            headers=headers,
            params={
                # Example params to fetch basic data
                "ids": "channel==MINE",
                "startDate": "2023-01-01",
                "endDate": "2023-12-31",
                "metrics": "views,estimatedMinutesWatched,averageViewDuration",
            },
        )

    if response.status_code != 200:
        return {
            "detail": "Failed to fetch YouTube Analytics",
            "status_code": response.status_code,
            "response": response.text,
        }

    data = response.json()
    return {
        "message": "Analytics dashboard data",
        "user": current_user["name"],
        "analytics": data,
    }


@router.get("/channel/{channel_id}")
async def get_channel_analytics(channel_id: str):
    """Get analytics for a specific channel"""
    return {
        "message": f"Channel analytics for {channel_id}",
        "channel_id": channel_id,
        "analytics": {},
    }


@router.get("/revenue")
async def get_revenue_analytics(days: Optional[int] = 30):
    """Get revenue analytics for specified period"""
    return {"message": f"Revenue analytics for {days} days", "revenue_data": []}
