from src.utils import replace_emoji_labels, replace_user_ids_and_channels, calculate_file_hash, resolve_file_name_conflict
import os
import tempfile
import shutil

def test_replace_emoji_labels():
    assert replace_emoji_labels(":+1:") == "👍"
    assert replace_emoji_labels(":joy:") == "😂"
    assert replace_emoji_labels("Hello :ok_hand:") == "Hello 👌"

def test_replace_user_ids_and_channels():
    def mock_get_user_display_name(user_id):
        return "Alex"
    assert replace_user_ids_and_channels("Hello <@U12345>", mock_get_user_display_name) == "Hello `@Alex`"
    assert replace_user_ids_and_channels("<!channel>", mock_get_user_display_name) == "`@channel`"
    assert replace_user_ids_and_channels("No mentions here", mock_get_user_display_name) == "No mentions here"

def test_calculate_file_hash():
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Hello, world!")
        temp_file_path = temp_file.name

    # Calculate the hash and verify it
    file_hash = calculate_file_hash(temp_file_path)
    assert file_hash == "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"

    # Clean up
    os.remove(temp_file_path)

def test_resolve_file_name_conflict():
    # Create a temporary folder
    temp_folder = tempfile.mkdtemp()

    # Simulate downloading a file to a temporary location
    temp_file_path = os.path.join(tempfile.gettempdir(), "test.txt")
    with open(temp_file_path, "w") as f:
        f.write("Hello, world!")

    # Test resolving a conflict with the same content
    # First, create a file in the target folder with the same content
    target_file_path = os.path.join(temp_folder, "test.txt")
    with open(target_file_path, "w") as f:
        f.write("Hello, world!")

    # Resolve the conflict
    resolved_file_path = resolve_file_name_conflict(temp_folder, "test.txt")

    # The function should reuse the existing file because the content is the same
    assert resolved_file_path == target_file_path

    # Test resolving a conflict with different content
    # Create a new temporary file with different content
    temp_file_path_2 = os.path.join(tempfile.gettempdir(), "test.txt")
    with open(temp_file_path_2, "w") as f:
        f.write("Different content")

    # Resolve the conflict
    resolved_file_path = resolve_file_name_conflict(temp_folder, "test.txt")

    # The function should create a new file with a timestamp suffix
    assert resolved_file_path != target_file_path
    assert resolved_file_path.endswith(".txt")
    assert os.path.exists(resolved_file_path)

    # Clean up
    shutil.rmtree(temp_folder)