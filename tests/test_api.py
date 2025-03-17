# test_api.py
from unittest.mock import patch
import pytest
from slack_sdk.errors import SlackApiError
from src.api import SlackAPI

@pytest.fixture
def mock_webclient():
    with patch('src.api.WebClient') as mock_client:  # Corrected patch target
        yield mock_client.return_value

def test_get_user_display_name_success(mock_webclient):
    mock_webclient.users_info.return_value = {
        "user": {
            "profile": {
                "display_name": "test_user",
                "real_name": "Real Name"
            }
        }
    }
    slack_api = SlackAPI("dummy_token")
    assert slack_api.get_user_display_name("U123") == "test_user"

def test_get_user_display_name_fallback(mock_webclient):
    mock_webclient.users_info.return_value = {
        "user": {
            "profile": {
                "display_name": "",
                "real_name": "Real Name"
            }
        }
    }
    slack_api = SlackAPI("dummy_token")
    assert slack_api.get_user_display_name("U123") == "Real Name"

def test_get_user_display_name_error(mock_webclient):
    mock_webclient.users_info.side_effect = SlackApiError("error", {"error": "invalid_auth"})
    slack_api = SlackAPI("dummy_token")
    assert slack_api.get_user_display_name("U123") == "Unknown User"