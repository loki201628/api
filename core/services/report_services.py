from fastapi import APIRouter, HTTPException, Response
from datetime import datetime
from core.handlers.excel_handler import generate_all_users_excel
from core.models.postgres_models import ActivityLog
from core.handlers.activity_handlers import log_activity
from utilities.mqtt_notifier import  send_excel_generated_message

router = APIRouter(prefix="/reports", tags=["Reports"])



@router.get("/export-all-users")
async def export_all_users_to_excel():
    """Export all users and their linked contacts to an Excel file"""
    try:
        # Log activity
        activity = ActivityLog(
            user_id="system",
            activity_type="EXPORT_ALL_USERS",
            description="Excel export generated for all users and their relationships"
        )
        log_activity(activity)

        # Generate Excel file
        excel_data = generate_all_users_excel()

        # ✅ Send MQTT notification after Excel generation
        send_excel_generated_message("All Users Excel exported")

        # Create a meaningful filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"all_users_contacts_{timestamp}.xlsx"

        # Return the Excel file as a download
        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Excel file: {str(e)}")
