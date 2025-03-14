import pytest
from unittest.mock import Mock, patch
from src.api import SlackAPI

@pytest.fixture
def slack_api():
    return SlackAPI("xoxp-dummy-token")

def test_get_user_info(slack_api):
    # Mock the Slack API response
    mock_response = {
        "user": {
            "profile": {
                "display_name": "Alex",
                "real_name": "Alex Smith"
            }
        }
    }
    slack_api.client.users_info = Mock(return_value=mock_response)

    # Test the function
    display_name = slack_api.get_user_info("U12345")
    assert display_name == "Alex"

def test_get_conversations_history(slack_api):
    # Mock the Slack API response
    mock_response = {
        "messages": [{"text": "Hello", "ts": "1234567890.123456"}],
        "response_metadata": {"next_cursor": None}
    }
    slack_api.client.conversations_history = Mock(return_value=mock_response)

    # Test the function
    messages, cursor = slack_api.get_conversations_history("C12345")
    assert len(messages) == 1
    assert messages[0]["text"] == "Hello"
    assert cursor is None

def test_get_conversations_replies(slack_api):
    # Mock the Slack API response
    mock_response = {
        "messages": [
            {"text": "Hello", "ts": "1234567890.123456"},
            {"text": "Hi", "ts": "1234567890.123457"}
        ]
    }
    slack_api.client.conversations_replies = Mock(return_value=mock_response)

    # Test the function
    replies = slack_api.get_conversations_replies("C12345", "1234567890.123456")
    assert len(replies) == 2
    assert replies[0]["text"] == "Hello"
    assert replies[1]["text"] == "Hi"