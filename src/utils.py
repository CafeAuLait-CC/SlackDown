import hashlib
import os
import shutil
import tempfile
from datetime import datetime

import emoji
import requests

# Emoji alias mapping for Slack-specific emojis
SLACK_EMOJI_MAPPING = {
    "+1": "👍",
    "-1": "👎",
    "joy": "😂",
    "exploding_head": "🤯",
    "ok_hand": "👌",
    "ok": "🆗",
    "white_check_mark": "✅",
    "zzz": "💤",
    "raised_hands": "🙌",
    "smiling_imp": "😈",
}


def replace_emoji_labels(text):
    """Replace emoji labels with actual emojis."""
    for alias, emoji_char in SLACK_EMOJI_MAPPING.items():
        text = text.replace(f":{alias}:", emoji_char)
    return emoji.emojize(text)


def replace_user_ids_and_channels(text, get_user_display_name):
    """Replace user IDs and channel mentions with display names."""
    if not text:
        return text
    words = text.split()
    for i, word in enumerate(words):
        if word.startswith("<@") and word.endswith(">"):
            user_id = word[2:-1]
            display_name = get_user_display_name(user_id)
            words[i] = f"`@{display_name}`"
        elif word == "<!channel>":
            words[i] = "`@channel`"
    return " ".join(words)


def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file's content."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def resolve_file_name_conflict(target_folder, file_name):
    """Resolve file name conflicts by checking content hashes."""
    os.makedirs(target_folder, exist_ok=True)
    temp_file_path = os.path.join(tempfile.gettempdir(), file_name)
    new_file_hash = calculate_file_hash(temp_file_path)

    for existing_file in os.listdir(target_folder):
        existing_file_path = os.path.join(target_folder, existing_file)
        if os.path.isfile(existing_file_path):
            existing_file_hash = calculate_file_hash(existing_file_path)
            if existing_file_hash == new_file_hash:
                os.remove(temp_file_path)
                return existing_file_path

    base_name, ext = os.path.splitext(file_name)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_file_path = os.path.join(target_folder, f"{base_name}-{timestamp}{ext}")
    shutil.move(temp_file_path, new_file_path)
    return new_file_path


def download_file(file_url, target_folder, file_name, token):
    """Download a file from Slack and resolve name conflicts."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(file_url, headers=headers, stream=True)
        if response.status_code == 200:
            temp_file_path = os.path.join(tempfile.gettempdir(), file_name)
            with open(temp_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            final_file_path = resolve_file_name_conflict(target_folder, file_name)
            return True, final_file_path
        else:
            print(f"Failed to download file: {file_name} (HTTP {response.status_code})")
            return False, None
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False, None
