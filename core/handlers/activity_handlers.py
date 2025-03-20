from core.models.postgres_models import ActivityLog, ActivityQuery
from config.database import get_db_session, contacts_collection, ActivityLogTable
from datetime import datetime
from fastapi import HTTPException


def log_activity(activity: ActivityLog):
    """Log a user activity to SQLite database using SQLAlchemy"""
    with get_db_session() as db:
        new_log = ActivityLogTable(
            user_id=activity.user_id,
            activity_type=activity.activity_type,
            description=activity.description,
            timestamp=activity.timestamp or datetime.now()
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log.id


def get_user_activities(query: ActivityQuery):
    """Get user activities from SQLite based on query parameters"""
    with get_db_session() as db:
        activity_query = db.query(ActivityLogTable)

        if query.user_id:
            activity_query = activity_query.filter(ActivityLogTable.user_id == query.user_id)

        if query.activity_type:
            activity_query = activity_query.filter(ActivityLogTable.activity_type == query.activity_type)

        if query.start_date:
            activity_query = activity_query.filter(ActivityLogTable.timestamp >= query.start_date)

        if query.end_date:
            activity_query = activity_query.filter(ActivityLogTable.timestamp <= query.end_date)

        activity_query = activity_query.order_by(ActivityLogTable.timestamp.desc())
        results = activity_query.all()

        return [
            {
                "id": a.id,
                "user_id": a.user_id,
                "activity_type": a.activity_type,
                "description": a.description,
                "timestamp": a.timestamp
            }
            for a in results
        ]


def get_contact_with_activities(user_id: str):
    """Get contact details from MongoDB and activity history from SQLite"""
    contact = contacts_collection.find_one({"user_id": user_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    with get_db_session() as db:
        activities = db.query(ActivityLogTable).filter(
            ActivityLogTable.user_id == user_id
        ).order_by(ActivityLogTable.timestamp.desc()).all()

    activity_list = [
        {
            "id": a.id,
            "user_id": a.user_id,
            "activity_type": a.activity_type,
            "description": a.description,
            "timestamp": a.timestamp
        }
        for a in activities
    ]

    return {
        "contact": contact,
        "activities": activity_list
    }
