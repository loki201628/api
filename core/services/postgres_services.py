from fastapi import APIRouter, HTTPException
from core.models.postgres_models import ActivityQuery
from core.handlers.activity_handlers import get_user_activities, get_contact_with_activities

router = APIRouter(prefix="/activities", tags=["Activity Tracking"])

@router.get("/user/{user_id}")
async def get_user_activity_history(user_id: str):
    """Get all activity logs for a specific user"""
    query = ActivityQuery(user_id=user_id)
    activities = get_user_activities(query)
    return {"activities": activities}

@router.post("/search")
async def search_activities(query: ActivityQuery):
    """Search for activities based on various criteria"""
    activities = get_user_activities(query)
    return {"activities": activities}

@router.get("/contact-with-history/{user_id}")
async def get_contact_details_with_history(user_id: str):
    """Get contact details from MongoDB with activity history from PostgreSQL"""
    result = get_contact_with_activities(user_id)
    return result