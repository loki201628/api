import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID
from core.handlers.contact_handlers import add_contact, get_all_contacts, update_contact, delete_contact
from core.models.contact_model import Contact
from core.models.postgres_models import ActivityLog
from fastapi import HTTPException

# Mock data
mock_contact = Contact(name="John Doe", email="john@example.com", phone=1234567890)
mock_user_id = "123e4567-e89b-12d3-a456-426614174000"
mock_contact_data = {
    "user_id": mock_user_id,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": 1234567890
}


@pytest.fixture
def mock_uuid():
    with patch('uuid.uuid4') as mock:
        mock.return_value = UUID(mock_user_id)
        yield mock


@pytest.fixture
def mock_contacts_collection():
    with patch('core.handlers.contact_handlers.contacts_collection') as mock:
        yield mock


@pytest.fixture
def mock_log_activity():
    with patch('core.handlers.contact_handlers.log_activity') as mock:
        yield mock


def test_add_contact(mock_uuid, mock_contacts_collection, mock_log_activity):
    # Configure the mock to properly return a value for insert_one
    mock_insert_result = MagicMock()
    mock_insert_result.acknowledged = True
    mock_contacts_collection.insert_one.return_value = mock_insert_result

    # Test adding a new contact
    result = add_contact(mock_contact)

    # Check if insert_one was called with right data
    mock_contacts_collection.insert_one.assert_called_once()
    insert_call_args = mock_contacts_collection.insert_one.call_args[0][0]
    assert insert_call_args["user_id"] == mock_user_id
    assert insert_call_args["name"] == "John Doe"
    assert insert_call_args["email"] == "john@example.com"
    assert insert_call_args["phone"] == 1234567890

    # Check if activity was logged
    mock_log_activity.assert_called_once()
    activity = mock_log_activity.call_args[0][0]
    assert isinstance(activity, ActivityLog)
    assert activity.user_id == mock_user_id
    assert activity.activity_type == "CONTACT_CREATED"

    # Check result
    assert result["message"] == "Contact added successfully"
    assert result["user_id"] == mock_user_id


def test_get_all_contacts(mock_contacts_collection):
    # Mock find() to return a list of contacts
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = [mock_contact_data]
    mock_contacts_collection.find.return_value = mock_cursor

    result = get_all_contacts()

    # Check if find was called with right parameters
    mock_contacts_collection.find.assert_called_once_with({}, {"_id": 0})

    # Check result
    assert len(result) == 1
    assert result[0] == mock_contact_data


def test_update_contact_success(mock_contacts_collection, mock_log_activity):
    # Mock find_one to return a contact
    mock_contacts_collection.find_one.return_value = mock_contact_data

    updated_data = {"name": "Jane Doe", "email": "jane@example.com"}

    result = update_contact(mock_user_id, updated_data)

    # Check if find_one was called
    mock_contacts_collection.find_one.assert_called_once_with({"user_id": mock_user_id})

    # Check if update_one was called with right parameters
    mock_contacts_collection.update_one.assert_called_once_with(
        {"user_id": mock_user_id},
        {"$set": updated_data}
    )

    # Check if activity was logged
    mock_log_activity.assert_called_once()
    activity = mock_log_activity.call_args[0][0]
    assert activity.activity_type == "CONTACT_UPDATED"

    # Check result
    assert result["message"] == "Contact updated successfully"
    assert result["updated_fields"] == updated_data


def test_update_contact_not_found(mock_contacts_collection):
    # Mock find_one to return None (contact not found)
    mock_contacts_collection.find_one.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        update_contact(mock_user_id, {"name": "Jane Doe"})

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Contact not found"


def test_update_contact_no_valid_fields(mock_contacts_collection):
    # Mock find_one to return a contact
    mock_contacts_collection.find_one.return_value = mock_contact_data

    # Empty update data or all None values
    with pytest.raises(HTTPException) as excinfo:
        update_contact(mock_user_id, {})

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "No valid fields to update"


def test_delete_contact_success(mock_contacts_collection, mock_log_activity):
    # Mock find_one to return a contact
    mock_contacts_collection.find_one.return_value = mock_contact_data

    result = delete_contact(mock_user_id)

    # Check if find_one was called
    mock_contacts_collection.find_one.assert_called_once_with({"user_id": mock_user_id})

    # Check if delete_one was called with right parameters
    mock_contacts_collection.delete_one.assert_called_once_with({"user_id": mock_user_id})

    # Check if activity was logged
    mock_log_activity.assert_called_once()
    activity = mock_log_activity.call_args[0][0]
    assert activity.activity_type == "CONTACT_DELETED"

    # Check result
    assert result["message"] == "Contact deleted successfully"


def test_delete_contact_not_found(mock_contacts_collection):
    # Mock find_one to return None (contact not found)
    mock_contacts_collection.find_one.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        delete_contact(mock_user_id)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Contact not found"