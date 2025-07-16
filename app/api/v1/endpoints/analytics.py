from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, List
from app.dependencies import get_current_user
from app.services.auth_service import auth_service
import httpx
from datetime import datetime, timedelta
import json

from app.utils.user_storage import user_storage

router = APIRouter()

YOUTUBE_DATA_URL = "https://www.googleapis.com/youtube/v3/channels"
YOUTUBE_ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"


def calculate_estimated_revenue(
    views: int, watch_time_minutes: int, region: str = "US"
) -> Dict:
    """
    Calculate estimated revenue based on views and watch time
    These are rough estimates based on industry averages
    """
    # RPM (Revenue Per Mille) varies by region and content type
    rpm_rates = {
        "US": {"min": 1.0, "max": 5.0, "avg": 2.5},
        "UK": {"min": 0.8, "max": 4.0, "avg": 2.0},
        "CA": {"min": 0.7, "max": 3.5, "avg": 1.8},
        "global": {"min": 0.3, "max": 2.0, "avg": 1.0},
    }

    rpm = rpm_rates.get(region, rpm_rates["global"])

    # Calculate estimated revenue
    estimated_revenue = {
        "ad_revenue": {
            "min": (views / 1000) * rpm["min"],
            "max": (views / 1000) * rpm["max"],
            "estimated": (views / 1000) * rpm["avg"],
        },
        "cpm": rpm["avg"],
        "total_monetizable_views": int(views * 0.6),  # Assuming 60% monetization rate
        "engagement_multiplier": (
            min(2.0, watch_time_minutes / (views * 3)) if views > 0 else 1.0
        ),
    }

    return estimated_revenue


def calculate_growth_metrics(current_data: Dict, previous_data: Dict) -> Dict:
    """Calculate growth percentages and trends"""
    growth = {}

    metrics = ["views", "estimatedMinutesWatched", "subscribersGained", "likes"]

    for metric in metrics:
        current_value = current_data.get(metric, 0)
        previous_value = previous_data.get(metric, 0)

        if previous_value > 0:
            growth[metric] = ((current_value - previous_value) / previous_value) * 100
        else:
            growth[metric] = 0

    return growth


@router.get("/dashboard")
async def get_dashboard_analytics(current_user: Dict = Depends(get_current_user)):
    try:
        user_tokens = user_storage.get_user_tokens(current_user["id"])
        if not user_tokens:
            raise HTTPException(status_code=401, detail="Google tokens not found")

        access_token = user_tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="Google access token missing")

        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            # Get Channel Info
            channel_response = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                headers=headers,
                params={
                    "part": "snippet,statistics,brandingSettings,contentDetails",
                    "mine": "true",
                },
            )

            if channel_response.status_code != 200:
                raise HTTPException(
                    status_code=500, detail="Failed to fetch channel info"
                )

            channel_data = channel_response.json()
            print(channel_data)
            channel = channel_data["items"][0]
            channel_id = channel["id"]

            # Get date ranges
            today = datetime.utcnow().date()
            last_30 = today - timedelta(days=30)
            last_60 = today - timedelta(days=60)
            last_90 = today - timedelta(days=90)

            # Get current period analytics (last 30 days)
            current_analytics_response = await client.get(
                "https://youtubeanalytics.googleapis.com/v2/reports",
                headers=headers,
                params={
                    "ids": "channel==MINE",
                    "startDate": str(last_30),
                    "endDate": str(today),
                    "metrics": "views,estimatedMinutesWatched,averageViewDuration,likes,subscribersGained,subscribersLost,estimatedRevenue,estimatedAdRevenue,cpm,playbackBasedCpm",
                },
            )

            # Get previous period analytics (30-60 days ago)
            previous_analytics_response = await client.get(
                "https://youtubeanalytics.googleapis.com/v2/reports",
                headers=headers,
                params={
                    "ids": "channel==MINE",
                    "startDate": str(last_60),
                    "endDate": str(last_30),
                    "metrics": "views,estimatedMinutesWatched,averageViewDuration,likes,subscribersGained,subscribersLost,estimatedRevenue,estimatedAdRevenue,cpm,playbackBasedCpm",
                },
            )

            # Get 90-day trend data
            trend_analytics_response = await client.get(
                "https://youtubeanalytics.googleapis.com/v2/reports",
                headers=headers,
                params={
                    "ids": "channel==MINE",
                    "startDate": str(last_90),
                    "endDate": str(today),
                    "metrics": "views,estimatedMinutesWatched,estimatedRevenue,subscribersGained",
                    "dimensions": "day",
                },
            )

            # Get top performing videos
            top_videos_response = await client.get(
                "https://youtubeanalytics.googleapis.com/v2/reports",
                headers=headers,
                params={
                    "ids": "channel==MINE",
                    "startDate": str(last_30),
                    "endDate": str(today),
                    "metrics": "views,estimatedMinutesWatched,estimatedRevenue,likes,comments",
                    "dimensions": "video",
                    "sort": "-views",
                    "maxResults": 10,
                },
            )

            # Get Playlists
            playlists_response = await client.get(
                "https://www.googleapis.com/youtube/v3/playlists",
                headers=headers,
                params={
                    "part": "snippet,contentDetails",
                    "channelId": channel_id,
                    "maxResults": 50,
                },
            )

            # Get Videos from Uploads Playlist
            uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"][
                "uploads"
            ]
            videos_response = await client.get(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                headers=headers,
                params={
                    "part": "snippet,contentDetails",
                    "playlistId": uploads_playlist_id,
                    "maxResults": 50,
                },
            )

            # Process analytics data
            current_analytics = (
                current_analytics_response.json()
                if current_analytics_response.status_code == 200
                else {"rows": []}
            )
            previous_analytics = (
                previous_analytics_response.json()
                if previous_analytics_response.status_code == 200
                else {"rows": []}
            )
            trend_analytics = (
                trend_analytics_response.json()
                if trend_analytics_response.status_code == 200
                else {"rows": []}
            )
            top_videos = (
                top_videos_response.json()
                if top_videos_response.status_code == 200
                else {"rows": []}
            )

            # Extract current period data
            current_data = {}
            if current_analytics.get("rows"):
                row = current_analytics["rows"][0]
                current_data = {
                    "views": row[0] if len(row) > 0 else 0,
                    "estimatedMinutesWatched": row[1] if len(row) > 1 else 0,
                    "averageViewDuration": row[2] if len(row) > 2 else 0,
                    "likes": row[3] if len(row) > 3 else 0,
                    "subscribersGained": row[4] if len(row) > 4 else 0,
                    "subscribersLost": row[5] if len(row) > 5 else 0,
                    "estimatedRevenue": row[6] if len(row) > 6 else 0,
                    "estimatedAdRevenue": row[7] if len(row) > 7 else 0,
                    "cpm": row[8] if len(row) > 8 else 0,
                    "playbackBasedCpm": row[9] if len(row) > 9 else 0,
                }

            # Extract previous period data
            previous_data = {}
            if previous_analytics.get("rows"):
                row = previous_analytics["rows"][0]
                previous_data = {
                    "views": row[0] if len(row) > 0 else 0,
                    "estimatedMinutesWatched": row[1] if len(row) > 1 else 0,
                    "estimatedRevenue": row[6] if len(row) > 6 else 0,
                    "subscribersGained": row[4] if len(row) > 4 else 0,
                }

            # Calculate growth metrics
            growth_metrics = calculate_growth_metrics(current_data, previous_data)

            # Calculate estimated revenue if YouTube Analytics doesn't provide it
            if current_data.get("estimatedRevenue", 0) == 0:
                estimated_revenue = calculate_estimated_revenue(
                    current_data.get("views", 0),
                    current_data.get("estimatedMinutesWatched", 0),
                )
                current_data["estimatedRevenue"] = estimated_revenue["ad_revenue"][
                    "estimated"
                ]
                current_data["cpm"] = estimated_revenue["cpm"]

            # Process trend data for charts
            trend_data = []
            if trend_analytics.get("rows"):
                for row in trend_analytics["rows"]:
                    trend_data.append(
                        {
                            "date": row[0],
                            "views": row[1],
                            "watchTime": row[2],
                            "revenue": row[3] if len(row) > 3 else 0,
                            "subscribers": row[4] if len(row) > 4 else 0,
                        }
                    )

            # Process top videos
            top_performing_videos = []
            if top_videos.get("rows"):
                for row in top_videos["rows"]:
                    top_performing_videos.append(
                        {
                            "videoId": row[0],
                            "views": row[1],
                            "watchTime": row[2],
                            "revenue": row[3] if len(row) > 3 else 0,
                            "likes": row[4] if len(row) > 4 else 0,
                            "comments": row[5] if len(row) > 5 else 0,
                        }
                    )

            # Calculate additional metrics
            watch_time_hours = current_data.get("estimatedMinutesWatched", 0) / 60
            rpm = (
                (
                    current_data.get("estimatedRevenue", 0)
                    / (current_data.get("views", 1) / 1000)
                )
                if current_data.get("views", 0) > 0
                else 0
            )

            # Calculate projected monthly revenue
            daily_revenue = current_data.get("estimatedRevenue", 0) / 30
            projected_monthly = daily_revenue * 30
            projected_yearly = projected_monthly * 12

            return {
                "message": "Complete Revenue & Analytics Dashboard",
                "user": current_user["name"],
                "channelData": {
                    "id": channel_id,
                    "title": channel["snippet"]["title"],
                    "description": channel["snippet"]["description"],
                    "thumbnails": channel["snippet"]["thumbnails"],
                    "totalViews": int(channel["statistics"]["viewCount"]),
                    "subscribers": int(channel["statistics"]["subscriberCount"]),
                    "totalVideos": int(channel["statistics"]["videoCount"]),
                    "watchTime": int(watch_time_hours),
                    "customUrl": channel["snippet"].get("customUrl", ""),
                    "publishedAt": channel["snippet"]["publishedAt"],
                },
                "analyticsData": {
                    "views": current_data.get("views", 0),
                    "estimatedMinutesWatched": current_data.get(
                        "estimatedMinutesWatched", 0
                    ),
                    "averageViewDuration": current_data.get("averageViewDuration", 0),
                    "likes": current_data.get("likes", 0),
                    "subscribersGained": current_data.get("subscribersGained", 0),
                    "subscribersLost": current_data.get("subscribersLost", 0),
                    "netSubscribers": current_data.get("subscribersGained", 0)
                    - current_data.get("subscribersLost", 0),
                },
                "revenueData": {
                    "currentPeriod": {
                        "estimatedRevenue": current_data.get("estimatedRevenue", 0),
                        "estimatedAdRevenue": current_data.get("estimatedAdRevenue", 0),
                        "cpm": current_data.get("cpm", 0),
                        "playbackBasedCpm": current_data.get("playbackBasedCpm", 0),
                        "rpm": rpm,
                    },
                    "projections": {
                        "daily": daily_revenue,
                        "monthly": projected_monthly,
                        "yearly": projected_yearly,
                    },
                    "growth": {
                        "revenueGrowth": growth_metrics.get("estimatedRevenue", 0),
                        "viewsGrowth": growth_metrics.get("views", 0),
                        "watchTimeGrowth": growth_metrics.get(
                            "estimatedMinutesWatched", 0
                        ),
                        "subscribersGrowth": growth_metrics.get("subscribersGained", 0),
                    },
                },
                "trendData": trend_data,
                "topVideos": top_performing_videos,
                "playlists": playlists_response.json().get("items", []),
                "videos": videos_response.json().get("items", []),
                "lastUpdated": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "message": "Error fetching analytics data",
            "error": str(e),
        }


@router.get("/revenue-breakdown")
async def get_revenue_breakdown(current_user: Dict = Depends(get_current_user)):
    """Get detailed revenue breakdown by traffic source, geography, etc."""
    user_tokens = user_storage.get_user_tokens(current_user["id"])
    if not user_tokens:
        raise HTTPException(status_code=401, detail="Google tokens not found")

    access_token = user_tokens.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}

    today = datetime.utcnow().date()
    last_30 = today - timedelta(days=30)

    async with httpx.AsyncClient() as client:
        # Revenue by traffic source
        traffic_source_response = await client.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            headers=headers,
            params={
                "ids": "channel==MINE",
                "startDate": str(last_30),
                "endDate": str(today),
                "metrics": "estimatedRevenue,views",
                "dimensions": "insightTrafficSourceType",
                "sort": "-estimatedRevenue",
            },
        )

        # Revenue by geography
        geography_response = await client.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            headers=headers,
            params={
                "ids": "channel==MINE",
                "startDate": str(last_30),
                "endDate": str(today),
                "metrics": "estimatedRevenue,views",
                "dimensions": "country",
                "sort": "-estimatedRevenue",
                "maxResults": 10,
            },
        )

        # Revenue by device type
        device_response = await client.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            headers=headers,
            params={
                "ids": "channel==MINE",
                "startDate": str(last_30),
                "endDate": str(today),
                "metrics": "estimatedRevenue,views",
                "dimensions": "deviceType",
                "sort": "-estimatedRevenue",
            },
        )

        return {
            "trafficSources": (
                traffic_source_response.json()
                if traffic_source_response.status_code == 200
                else {"rows": []}
            ),
            "geography": (
                geography_response.json()
                if geography_response.status_code == 200
                else {"rows": []}
            ),
            "devices": (
                device_response.json()
                if device_response.status_code == 200
                else {"rows": []}
            ),
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
