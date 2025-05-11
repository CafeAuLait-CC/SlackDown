import os
import hashlib
import shutil
import tempfile
import requests

from datetime import datetime
from src.config import load_config


def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file's content."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def calculate_url_hash(url):
    return hashlib.sha256(url).hexdigest()[:16]


def resolve_file_name_conflict(target_folder, file_name):
    """Resolve file name conflicts by checking content hashes."""
    # Create the target folder if it doesn't exist
    os.makedirs(target_folder, exist_ok=True)

    # Calculate the hash of the new file (downloaded to a temporary location)
    temp_file_path = os.path.join(tempfile.gettempdir(), file_name)
    new_file_hash = calculate_file_hash(temp_file_path)

    # Check if a file with the same content already exists in the target folder
    for existing_file in os.listdir(target_folder):
        existing_file_path = os.path.join(target_folder, existing_file)
        if os.path.isfile(existing_file_path):
            existing_file_hash = calculate_file_hash(existing_file_path)
            if existing_file_hash == new_file_hash:
                # Reuse the existing file and delete the temporary file
                os.remove(temp_file_path)
                return existing_file_path  # Return the path of the existing file

    # If no matching file is found, move the temporary file to the target folder
    # and append a timestamp suffix to avoid conflicts
    base_name, ext = os.path.splitext(file_name)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_file_path = os.path.join(target_folder, f"{base_name}-{timestamp}{ext}")
    shutil.move(temp_file_path, new_file_path)
    return new_file_path


def download_file(file_url, target_folder, file_name):
    try:
        config = load_config()
        headers = {"Authorization": f"Bearer {config['slack_token']}"}
        response = requests.get(file_url, headers=headers, stream=True)
        if response.status_code == 200:
            # Download the file to a temporary location
            temp_file_path = os.path.join(tempfile.gettempdir(), file_name)
            with open(temp_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Resolve file name conflicts and move the file to the target folder
            final_file_path = resolve_file_name_conflict(target_folder, file_name)
            return True, final_file_path
        else:
            print(f"Failed to download file: {file_name} (HTTP {response.status_code})")
            return False, None
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False, None
