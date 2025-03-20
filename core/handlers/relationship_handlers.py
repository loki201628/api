from core.models.relationship_model import ContactRelationship, ContactRelationshipBulk
from core.models.postgres_models import ActivityLog
from core.handlers.activity_handlers import log_activity
from config.database import get_db_session, contacts_collection, ContactRelationshipTable
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List


def add_contact_relationship(relationship: ContactRelationship):
    """Add a relationship between a user email and a contact"""
    contact = contacts_collection.find_one({"user_id": relationship.linked_user_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Linked contact not found")

    with get_db_session() as db:
        try:
            new_rel = ContactRelationshipTable(
                owner_email=relationship.owner_email,
                linked_user_id=relationship.linked_user_id,
                relationship_type=relationship.relationship_type
            )
            db.add(new_rel)
            db.commit()
            db.refresh(new_rel)

            activity = ActivityLog(
                user_id=relationship.linked_user_id,
                activity_type="RELATIONSHIP_ADDED",
                description=f"Contact linked to {relationship.owner_email}"
            )
            log_activity(activity)
            return new_rel.id

        except IntegrityError:
            db.rollback()
            existing_rel = db.query(ContactRelationshipTable).filter(
                ContactRelationshipTable.owner_email == relationship.owner_email,
                ContactRelationshipTable.linked_user_id == relationship.linked_user_id
            ).first()

            if existing_rel:
                existing_rel.relationship_type = relationship.relationship_type
                db.commit()
                activity = ActivityLog(
                    user_id=relationship.linked_user_id,
                    activity_type="RELATIONSHIP_UPDATED",
                    description=f"Contact relationship with {relationship.owner_email} updated"
                )
                log_activity(activity)
                return existing_rel.id


def add_bulk_relationships(bulk_data: ContactRelationshipBulk):
    added_count = 0
    failed_ids = []

    for user_id in bulk_data.linked_user_ids:
        try:
            relationship = ContactRelationship(
                owner_email=bulk_data.owner_email,
                linked_user_id=user_id,
                relationship_type=bulk_data.relationship_type
            )
            add_contact_relationship(relationship)
            added_count += 1
        except HTTPException:
            failed_ids.append(user_id)

    return {"added_count": added_count, "failed_ids": failed_ids}


def remove_contact_relationship(owner_email: str, linked_user_id: str):
    with get_db_session() as db:
        rel = db.query(ContactRelationshipTable).filter(
            ContactRelationshipTable.owner_email == owner_email,
            ContactRelationshipTable.linked_user_id == linked_user_id
        ).first()

        if not rel:
            raise HTTPException(status_code=404, detail="Relationship not found")

        db.delete(rel)
        db.commit()

        activity = ActivityLog(
            user_id=linked_user_id,
            activity_type="RELATIONSHIP_REMOVED",
            description=f"Contact unlinked from {owner_email}"
        )
        log_activity(activity)
        return {"message": "Relationship removed successfully"}


def get_linked_contacts(owner_email: str):
    with get_db_session() as db:
        relationships = db.query(ContactRelationshipTable).filter(
            ContactRelationshipTable.owner_email == owner_email
        ).all()

    if not relationships:
        return []

    user_ids = [rel.linked_user_id for rel in relationships]
    relationship_map = {rel.linked_user_id: rel.relationship_type for rel in relationships}
    linked_contacts = list(contacts_collection.find({"user_id": {"$in": user_ids}}, {"_id": 0}))

    for contact in linked_contacts:
        contact["relationship_type"] = relationship_map.get(contact["user_id"])

    return linked_contacts
