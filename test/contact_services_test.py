import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from core.services.contact_services import (
    add_new_contact,
    fetch_all_contacts,
    update_contact_details,
    delete_contact_details
)
from core.models.contact_model import Contact

# Mock data
mock_contact = Contact(name="John Doe", email="john@example.com", phone=1234567890)
mock_user_id = "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def mock_add_contact():
    with patch('core.services.contact_services.add_contact') as mock:
        mock.return_value = {"message": "Contact added successfully", "user_id": mock_user_id}
        yield mock


@pytest.fixture
def mock_get_all_contacts():
    with patch('core.services.contact_services.get_all_contacts') as mock:
        mock.return_value = [
            {"user_id": mock_user_id, "name": "John Doe", "email": "john@example.com", "phone": 1234567890}
        ]
        yield mock


@pytest.fixture
def mock_update_contact():
    with patch('core.services.contact_services.update_contact') as mock:
        mock.return_value = {"message": "Contact updated successfully", "updated_fields": {"name": "Jane Doe"}}
        yield mock


@pytest.fixture
def mock_delete_contact():
    with patch('core.services.contact_services.delete_contact') as mock:
        mock.return_value = {"message": "Contact deleted successfully"}
        yield mock


@pytest.mark.asyncio
async def test_add_new_contact(mock_add_contact):
    result = await add_new_contact(mock_contact)

    # Check if handler was called with right data
    mock_add_contact.assert_called_once_with(mock_contact)

    # Check result
    assert result["message"] == "Contact added successfully"
    assert result["user_id"] == mock_user_id


@pytest.mark.asyncio
async def test_fetch_all_contacts(mock_get_all_contacts):
    result = await fetch_all_contacts()

    # Check if handler was called
    mock_get_all_contacts.assert_called_once()

    # Check result
    assert "contacts" in result
    assert len(result["contacts"]) == 1
    assert result["contacts"][0]["user_id"] == mock_user_id


@pytest.mark.asyncio
async def test_update_contact_details(mock_update_contact):
    updated_data = {"name": "Jane Doe"}
    result = await update_contact_details(mock_user_id, updated_data)

    # Check if handler was called with right data
    mock_update_contact.assert_called_once_with(mock_user_id, updated_data)

    #