from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class ContactRelationship(BaseModel):
    owner_email: EmailStr
    linked_user_id: str
    relationship_type: Optional[str] = None

class ContactRelationshipBulk(BaseModel):
    owner_email: EmailStr
    linked_user_ids: List[str]
    relationship_type: Optional[str] = None

class LinkedContact(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    phone: int
    relationship_type: Optional[str] = None