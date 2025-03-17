# test_slackdown.py
from unittest.mock import patch, MagicMock
import pytest
from slackdown import backup_all_messages

@patch('slackdown.SlackAPI')
@patch('slackdown.fetch_and_save_messages')
def test_backup_all_messages(mock_fetch, mock_slack):
    config = {
        "slack_token": "dummy",
        "backup_list": ["general"],
        "direct_msg_dir": "dm",
        "group_msg_dir": "groups",
        "channel_msg_dir": "channels",
        "attachments_dir": "attachments",
        "backup_attachments": True
    }
    
    # Mock user display name for IM channel
    mock_slack_instance = MagicMock()
    mock_slack_instance.get_user_display_name.return_value = "general"
    mock_slack.return_value = mock_slack_instance
    
    mock_slack.return_value.get_conversations_list.side_effect = [
        [{"name": "general", "id": "C123"}],  # public
        [],  # private
        [],  # mpim
        [{"user": "U123", "id": "D123"}]      # im
    ]
    
    backup_all_messages(config)
    assert mock_fetch.call_count == 2  # public channel + IM