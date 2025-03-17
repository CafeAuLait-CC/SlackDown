# test_helper.py
import os
import tempfile
from unittest.mock import Mock, patch
import pytest
from src.helper import download_file, resolve_file_name_conflict

@patch('src.helper.requests.get')
@patch('src.helper.load_config')
def test_download_file_success(mock_load_config, mock_get, tmpdir):
    mock_load_config.return_value = {"slack_token": "dummy"}
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"test content"]
    mock_get.return_value = mock_response
    
    success, path = download_file("http://example.com/file.txt", str(tmpdir), "file.txt")
    assert success is True
    assert os.path.exists(path)

def test_resolve_file_name_conflict(tmpdir, monkeypatch):
    # Mock tempfile.gettempdir() to use test directory
    monkeypatch.setattr(tempfile, 'gettempdir', lambda: str(tmpdir))
    
    target_folder = str(tmpdir)
    test_file = tmpdir.join("existing.txt")
    test_file.write("same content")
    
    # Create temp file with same content in system temp dir (now mocked to tmpdir)
    temp_file = tmpdir.join("temp.txt")
    temp_file.write("same content")
    
    result = resolve_file_name_conflict(target_folder, "temp.txt")
    assert os.path.basename(result) == "existing.txt"