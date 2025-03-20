from fastapi import APIRouter, HTTPException
from core.models.contact_model import Contact
from core.handlers.contact_handlers import add_contact, get_all_contacts, update_contact, delete_contact

router = APIRouter(prefix="/contact", tags=["Contact Management"])

@router.post("/add")
async def add_new_contact(contact: Contact):
    response = add_contact(contact)
    return response

@router.get("/all")
async def fetch_all_contacts():
    contacts = get_all_contacts()
    return {"contacts": contacts}

@router.put("/update/{user_id}")
async def update_contact_details(user_id: str, updated_data: dict):
    response = update_contact(user_id, updated_data)
    return response

@router.delete("/delete/{user_id}")
async def delete_contact_details(user_id: str):
    response = delete_contact(user_id)
    return response

