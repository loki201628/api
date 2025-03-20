import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from core.handlers.relationship_handlers import (
    add_contact_relationship,
    add_bulk_relationships,
    remove_contact_relationship,
    get_linked_contacts
)
from core.models.relationship_model import ContactRelationship, ContactRelationshipBulk

# Mock data
mock_user_id = "123e4567-e89b-12d3-a456-426614174000"
mock_owner_email = "owner@example.com"
mock_relationship = ContactRelationship(
    owner_email=mock_owner_email,
    linked_user_id=mock_user_id,
    relationship_type="Friend"
)
mock_contact_data = {
    "user_id": mock_user_id,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": 1234567890
}

@pytest.fixture
def mock_db_session():
    with patch('core.handlers.relationship_handlers.get_db_session') as mock:
        mock_session = MagicMock()
        mock.__enter__.return_value = mock_session
        yield mock, mock_session

@pytest.fixture
def mock_contacts_collection():
    with patch('core.handlers.relationship_handlers.contacts_collection') as mock:
        yield mock

@pytest.fixture
def mock_log_activity():
    with patch('core.handlers.relationship_handlers.log_activity') as mock:
        yield mock

def test_add_contact_relationship_success(mock_db_session, mock_contacts_collection, mock_log_activity):
    _, mock_session = mock_db_session

    mock_contacts_collection.find_one.return_value = mock_contact_data
    mock_session.add.return_value = None
    mock_session.commit.return_value = None

    relationship_id = add_contact_relationship(mock_relationship)

    mock_contacts_collection.find_one.assert_called_once_with({"user_id": mock_user_id})
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_log_activity.assert_called_once()
    assert relationship_id is not None

def test_add_contact_relationship_not_found(mock_contacts_collection):
    mock_contacts_collection.find_one.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        add_contact_relationship(mock_relationship)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Linked contact not found"

def test_add_bulk_relationships(mock_contacts_collection):
    with patch('core.handlers.relationship_handlers.add_contact_relationship') as mock_add:
        def side_effect(rel):
            if rel.linked_user_id == "id1":
                return 1
            else:
                raise HTTPException(status_code=404, detail="Contact not found")

        mock_add.side_effect = side_effect

        bulk_data = ContactRelationshipBulk(
            owner_email=mock_owner_email,
            linked_user_ids=["id1", "id2"],
            relationship_type="Friend"
        )

        result = add_bulk_relationships(bulk_data)

        assert result["added_count"] == 1
        assert result["failed_ids"] == ["id2"]

def test_remove_contact_relationship_success(mock_db_session, mock_log_activity):
    _, mock_session = mock_db_session

    mock_session.query().filter().first.return_value = True
    result = remove_contact_relationship(mock_owner_email, mock_user_id)

    mock_session.query().filter().delete.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_log_activity.assert_called_once()
    assert result["message"] == "Relationship removed successfully"

def test_remove_contact_relationship_not_found(mock_db_session):
    _, mock_session = mock_db_session

    mock_session.query().filter().first.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        remove_contact_relationship(mock_owner_email, mock_user_id)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Relationship not found"

def test_get_linked_contacts_empty(mock_db_session):
    _, mock_session = mock_db_session
    mock_session.query().filter().all.return_value = []
    result = get_linked_contacts(mock_owner_email)
    assert result == []

def test_get_linked_contacts_with_data(mock_db_session, mock_contacts_collection):
    _, mock_session = mock_db_session

    mock_session.query().filter().all.return_value = [
        MagicMock(linked_user_id="id1", relationship_type="Friend"),
        MagicMock(linked_user_id="id2", relationship_type="Colleague")
    ]

    mock_contacts_cursor = MagicMock()
    mock_contacts_cursor.__iter__.return_value = [
        {"user_id": "id1", "name": "John", "email": "john@example.com", "phone": 1234567890},
        {"user_id": "id2", "name": "Jane", "email": "jane@example.com", "phone": 9876543210}
    ]
    mock_contacts_collection.find.return_value = mock_contacts_cursor

    result = get_linked_contacts(mock_owner_email)

    assert len(result) == 2
    assert result[0]["user_id"] == "id1"
    assert result[0]["relationship_type"] == "Friend"
    assert result[1]["user_id"] == "id2"
    assert result[1]["relationship_type"] == "Colleague"
