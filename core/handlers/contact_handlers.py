from core.models.contact_model import Contact
from core.models.postgres_models import ActivityLog
from core.handlers.activity_handlers import log_activity
from config.database import contacts_collection
from uuid import uuid4
from fastapi import HTTPException, Depends
from datetime import datetime


def add_contact(contact: Contact):
    user_id = str(uuid4())  # Generate unique User ID
    contact_data = {
        "user_id": user_id,
        "name": contact.name,
        "email": contact.email,
        "phone": contact.phone
    }
    contacts_collection.insert_one(contact_data)

    # Log activity in PostgreSQL
    activity = ActivityLog(
        user_id=user_id,
        activity_type="CONTACT_CREATED",
        description=f"New contact created for {contact.name}"
    )
    log_activity(activity)

    return {"message": "Contact added successfully", "user_id": user_id}


def get_all_contacts():
    contacts = list(contacts_collection.find({}, {"_id": 0}))  # Exclude MongoDB's default _id field
    return contacts


def update_contact(user_id: str, updated_data: dict):
    contact = contacts_collection.find_one({"user_id": user_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_fields = {key: value for key, value in updated_data.items() if value is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    contacts_collection.update_one({"user_id": user_id}, {"$set": update_fields})

    # Log activity in PostgreSQL
    field_list = ", ".join(update_fields.keys())
    activity = ActivityLog(
        user_id=user_id,
        activity_type="CONTACT_UPDATED",
        description=f"Updated contact fields: {field_list}"
    )
    log_activity(activity)

    return {"message": "Contact updated successfully", "updated_fields": update_fields}


def delete_contact(user_id: str):
    contact = contacts_collection.find_one({"user_id": user_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contacts_collection.delete_one({"user_id": user_id})

    # Log activity in PostgreSQL
    activity = ActivityLog(
        user_id=user_id,
        activity_type="CONTACT_DELETED",
        description=f"Contact deleted: {contact['name']}"
    )
    log_activity(activity)

    return {"message": "Contact deleted successfully"}