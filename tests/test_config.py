# test_config.py
import configparser
from unittest.mock import patch
import pytest
from src.config import load_config

@pytest.fixture
def mock_config(tmpdir, monkeypatch):
    config_content = """
    [Slack]
    User_OAuth_Token = xoxp-123456
    
    [Directories]
    Direct_Msg_Directory = test_dm
    Group_Msg_Directory = test_groups
    Channel_Msg_Directory = test_channels
    Attachment_Directory = test_attachments
    
    [Options]
    Backup_Attachments = True
    Backup_List = general,random
    """
    config_file = tmpdir.join("config.txt")
    config_file.write(config_content)
    monkeypatch.chdir(tmpdir)  # Ensure current directory is tmpdir
    return config_file

def test_load_config_valid(mock_config):
    config = load_config()
    assert config["slack_token"] == "xoxp-123456"
    assert config["direct_msg_dir"] == "test_dm"

def test_load_config_defaults(tmpdir, monkeypatch):
    config_content = """
    [Slack]
    User_OAuth_Token = xoxp-123456
    """
    config_file = tmpdir.join("config.txt")
    config_file.write(config_content)
    monkeypatch.chdir(tmpdir)  # Switch to tmpdir
    config = load_config()
    assert config["direct_msg_dir"] == "dm"