from fastapi import APIRouter, HTTPException, Response
from datetime import datetime
from core.models.relationship_model import ContactRelationship, ContactRelationshipBulk
from core.handlers.relationship_handlers import (
    add_contact_relationship,
    add_bulk_relationships,
    remove_contact_relationship,
    get_linked_contacts
)
from core.handlers.excel_handler import generate_all_users_excel
from core.models.postgres_models import ActivityLog
from core.handlers.activity_handlers import log_activity
from pydantic import EmailStr

router = APIRouter(prefix="/contacts/relationships", tags=["Contact Relationships"])


@router.post("/link")
async def link_contact(relationship: ContactRelationship):
    """Link a contact to a user by email"""
    relationship_id = add_contact_relationship(relationship)
    return {
        "message": "Contact linked successfully",
        "relationship_id": relationship_id
    }


@router.post("/link-bulk")
async def link_multiple_contacts(bulk_data: ContactRelationshipBulk):
    """Link multiple contacts to a user by email in a single operation"""
    result = add_bulk_relationships(bulk_data)
    return {
        "message": f"Added {result['added_count']} relationships",
        "failed_ids": result["failed_ids"]
    }


@router.delete("/unlink")
async def unlink_contact(owner_email: EmailStr, linked_user_id: str):
    """Remove a link between a contact and a user"""
    result = remove_contact_relationship(owner_email, linked_user_id)
    return result


@router.get("/linked/{owner_email}")
async def get_linked_contact_list(owner_email: EmailStr):
    """Get all contacts linked to a specific user email"""
    contacts = get_linked_contacts(owner_email)
    return {"linked_contacts": contacts, "count": len(contacts)}


@router.get("/export-excel/{owner_email}")
async def export_contacts_to_excel(owner_email: EmailStr):
    """Export linked contacts for a specific user to an Excel file"""
    try:
        # Log activity
        activity = ActivityLog(
            user_id="system",
            activity_type="EXPORT_EXCEL",
            description=f"Excel export generated for {owner_email}"
        )
        log_activity(activity)

        # Generate Excel file
        excel_data = generate_contacts_excel(owner_email)

        # Create a meaningful filename with timestamp
        filename = f"contacts_{owner_email.replace('@', '_at_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # Return the Excel file as a download
        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException as e:
        # Re-raise the exception to maintain the status code and detail
        raise e
    except Exception as e:
        # For any other errors, return a 500 error
        raise HTTPException(status_code=500, detail=f"Error generating Excel file: {str(e)}")