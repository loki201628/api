import io
import xlsxwriter
from datetime import datetime
from fastapi import HTTPException
from core.handlers.relationship_handlers import get_linked_contacts
from config.database import contacts_collection, get_db_session, ContactRelationshipTable


def generate_all_users_excel():
    try:
        all_users = list(contacts_collection.find({}, {"_id": 0}))
        if not all_users:
            raise HTTPException(status_code=404, detail="No users found in the database")

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        summary_sheet = workbook.add_worksheet("Users Summary")
        details_sheet = workbook.add_worksheet("Contact Details")

        summary_sheet.write(0, 0, "Contact Management System - Users Summary")
        summary_sheet.write(1, 0, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        summary_headers = ["User ID", "Name", "Email", "Phone", "Linked Contacts"]
        for col_num, header in enumerate(summary_headers):
            summary_sheet.write(3, col_num, header)

        user_linked_counts = {}
        user_emails = [user.get("email", "") for user in all_users if user.get("email")]

        try:
            with get_db_session() as db:
                result = db.query(ContactRelationshipTable.owner_email).all()
                if user_emails:
                    for email in user_emails:
                        count = db.query(ContactRelationshipTable).filter(
                            ContactRelationshipTable.owner_email == email
                        ).count()
                        user_linked_counts[email] = count
        except Exception as e:
            print(f"Error fetching relationship counts: {e}")

        for row_num, user in enumerate(all_users, start=4):
            user_id = user.get("user_id", "N/A")
            name = user.get("name", "N/A")
            email = user.get("email", "N/A")
            phone = str(user.get("phone", "N/A"))

            summary_sheet.write(row_num, 0, user_id)
            summary_sheet.write(row_num, 1, name)
            summary_sheet.write(row_num, 2, email)
            summary_sheet.write(row_num, 3, phone)
            linked_count = user_linked_counts.get(email, 0)
            summary_sheet.write(row_num, 4, linked_count)

        summary_sheet.write(len(all_users) + 5, 0, f"Total Users: {len(all_users)}")

        details_sheet.write(0, 0, "Contact Management System - Detailed Relationships")
        details_sheet.write(1, 0, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        details_headers = ["Owner Email", "User ID", "Name", "Email", "Phone", "Relationship Type"]
        for col_num, header in enumerate(details_headers):
            details_sheet.write(3, col_num, header)

        user_map = {user.get("user_id", ""): user for user in all_users if user.get("user_id")}

        all_relationships = []
        try:
            with get_db_session() as db:
                all_relationships = db.query(ContactRelationshipTable).order_by(ContactRelationshipTable.owner_email).all()
        except Exception as e:
            print(f"Error fetching relationships: {e}")

        row_num = 4
        for rel in all_relationships:
            try:
                owner_email = rel.owner_email
                linked_user_id = rel.linked_user_id
                relationship_type = rel.relationship_type or "Not specified"

                if linked_user_id in user_map:
                    contact = user_map[linked_user_id]

                    details_sheet.write(row_num, 0, owner_email)
                    details_sheet.write(row_num, 1, linked_user_id)
                    details_sheet.write(row_num, 2, contact.get("name", "N/A"))
                    details_sheet.write(row_num, 3, contact.get("email", "N/A"))
                    details_sheet.write(row_num, 4, str(contact.get("phone", "N/A")))
                    details_sheet.write(row_num, 5, relationship_type)
                    row_num += 1
            except Exception as e:
                print(f"Error processing relationship: {e}")
                continue

        details_sheet.write(row_num + 1, 0, f"Total Relationships: {len(all_relationships)}" if all_relationships else "No relationships found")

        workbook.close()
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")
