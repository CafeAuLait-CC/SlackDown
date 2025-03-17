# test_message_processor.py
import os
from unittest.mock import Mock, patch
import pytest
from src.message_processor import fetch_and_save_messages

@patch('src.message_processor.SlackAPI')
@patch('src.message_processor.load_config')
def test_fetch_and_save_messages(mock_load_config, mock_slack, tmpdir):
    mock_config = {
        "slack_token": "dummy",
        "direct_msg_dir": str(tmpdir),
        "channel_msg_dir": str(tmpdir),  # Added required keys
        "group_msg_dir": str(tmpdir),
        "attachments_dir": str(tmpdir),
        "backup_attachments": False
    }
    mock_load_config.return_value = mock_config
    
    mock_slack.return_value.get_conversations_history.return_value = [{
        "ts": "1234567890.123456",
        "user": "U123",
        "text": "Hello world"
    }]
    
    fetch_and_save_messages("C123", "test_channel", "public_channel")
    
    expected_file = os.path.join(str(tmpdir), "test_channel.md")
    assert os.path.exists(expected_file)