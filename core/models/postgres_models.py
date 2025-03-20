from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ActivityLog(BaseModel):
    user_id: str
    activity_type: str
    description: Optional[str] = None
    timestamp: Optional[datetime] = None


class ActivityQuery(BaseModel):
    user_id: Optional[str] = None
    activity_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None