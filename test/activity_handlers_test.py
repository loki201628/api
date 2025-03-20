import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from core.handlers.activity_handlers import log_activity, get_user_activities, get_contact_with_activities
from core.models.postgres_models import ActivityLog, ActivityQuery
from fastapi import HTTPException
import psycopg2

# Mock data
mock_user_id = "123e4567-e89b-12d3-a456-426614174000"
mock_activity = ActivityLog(
    user_id=mock_user_id,
    activity_type="TEST_ACTIVITY",
    description="Test activity description"
)
mock_timestamp = datetime(2025, 1, 1, 12, 0, 0)


@pytest.fixture
def mock_pg_connection():
    with patch('core.handlers.activity_handlers.get_pg_connection') as mock:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock.return_value = mock_conn
        yield mock, mock_conn, mock_cursor


@pytest.fixture
def mock_contacts_collection():
    with patch('core.handlers.activity_handlers.contacts_collection') as mock:
        yield mock


def test_log_activity(mock_pg_connection):
    _, mock_conn, mock_cursor = mock_pg_connection

    # Mock cursor.fetchone to return an ID
    mock_cursor.fetchone.return_value = [1]

    # Test with no timestamp
    activity_id = log_activity(mock_activity)

    # Check if execute was called with right parameters
    mock_cursor.execute.assert_called_once()
    # Get the SQL and parameters from the call
    sql, params = mock_cursor.execute.call_args[0]
    assert "INSERT INTO activity_logs" in sql
    assert params[0] == mock_user_id
    assert params[1] == "TEST_ACTIVITY"
    assert params[2] == "Test activity description"

    # Check if commit was called
    mock_conn.commit.assert_called_once()

    # Check result
    assert activity_id == 1


def test_log_activity_with_timestamp(mock_pg_connection):
    _, mock_conn, mock_cursor = mock_pg_connection

    # Mock cursor.fetchone to return an ID
    mock_cursor.fetchone.return_value = [1]

    # Create an activity with a specific timestamp
    activity_with_timestamp = ActivityLog(
        user_id=mock_user_id,
        activity_type="TEST_ACTIVITY",
        description="Test activity description",
        timestamp=mock_timestamp
    )

    activity_id = log_activity(activity_with_timestamp)

    # Check if timestamp was used
    sql, params = mock_cursor.execute.call_args[0]
    assert params[3] == mock_timestamp

    # Check result
    assert activity_id == 1


def test_get_user_activities_no_filters(mock_pg_connection):
    _, _, mock_cursor = mock_pg_connection

    # Mock expected return value
    mock_cursor.fetchall.return_value = [
        {"id": 1, "user_id": mock_user_id, "activity_type": "TEST_ACTIVITY"}
    ]

    # Create empty query
    query = ActivityQuery()

    results = get_user_activities(query)

    # Check SQL has no WHERE clause
    sql, params = mock_cursor.execute.call_args[0]
    assert "WHERE" not in sql
    assert "ORDER BY timestamp DESC" in sql
    assert not params  # No parameters for an empty query

    # Check result
    assert len(results) == 1
    assert results[0]["user_id"] == mock_user_id


def test_get_user_activities_with_filters(mock_pg_connection):
    _, _, mock_cursor = mock_pg_connection

    # Create query with filters
    query = ActivityQuery(
        user_id=mock_user_id,
        activity_type="TEST_ACTIVITY",
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31)
    )

    results = get_user_activities(query)

    # Check SQL has WHERE clause with conditions
    sql, params = mock_cursor.execute.call_args[0]
    assert "WHERE" in sql
    assert "user_id = %s" in sql
    assert "activity_type = %s" in sql
    assert "timestamp >= %s" in sql
    assert "timestamp <= %s" in sql
    assert params == [mock_user_id, "TEST_ACTIVITY", datetime(2025, 1, 1), datetime(2025, 1, 31)]


def test_get_contact_with_activities_success(mock_pg_connection, mock_contacts_collection):
    _, _, mock_cursor = mock_pg_connection

    # Mock MongoDB find_one
    mock_contacts_collection.find_one.return_value = {
        "user_id": mock_user_id,
        "name": "John Doe",
        "email": "john@example.com"
    }

    # Mock PostgreSQL activity logs
    mock_cursor.fetchall.return_value = [
        {"id": 1, "user_id": mock_user_id, "activity_type": "TEST_ACTIVITY"}
    ]

    result = get_contact_with_activities(mock_user_id)

    # Check MongoDB query
    mock_contacts_collection.find_one.assert_called_once_with(
        {"user_id": mock_user_id},
        {"_id": 0}
    )

    # Check PostgreSQL query
    sql, params = mock_cursor.execute.call_args[0]
    assert "SELECT * FROM activity_logs WHERE user_id = %s" in sql
    assert params == (mock_user_id,)

    # Check result structure
    assert "contact" in result
    assert "activities" in result
    assert result["contact"]["user_id"] == mock_user_id
    assert len(result["activities"]) == 1


def test_get_contact_with_activities_not_found(mock_pg_connection, mock_contacts_collection):
    # Mock MongoDB find_one to return None
    mock_contacts_collection.find_one.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        get_contact_with_activities(mock_user_id)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Contact not found"