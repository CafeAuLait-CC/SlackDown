import os
import certifi
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time
from datetime import datetime
import requests
import configparser
import emoji
import hashlib
import shutil
import tempfile


os.environ["SSL_CERT_FILE"] = certifi.where()

# Load configuration from config.txt
config = configparser.ConfigParser()
config.read("config.txt")

# Slack token
SLACK_TOKEN = config.get("Slack", "User_OAuth_Token")

# Directories
DIRECT_MSG_DIRECTORY = config.get("Directories", "Direct_Msg_Directory", fallback="dm")
GROUP_MSG_DIRECTORY = config.get("Directories", "Group_Msg_Directory", fallback="groups")
CHANNEL_MSG_DIRECTORY = config.get("Directories", "Channel_Msg_Directory", fallback="channels")
ATTACHMENTS_DIRECTORY = config.get("Directories", "Attachment_Directory", fallback="attachments")

# Backup options
BACKUP_ATTACHMENTS = config.getboolean("Options", "Backup_Attachments", fallback=True)
BACKUP_LIST = config.get("Options", "Backup_List", fallback="all").split(",")

# Initialize Slack client
client = WebClient(token=SLACK_TOKEN)

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
    # Add more mappings as needed
}

# Function to get user info by ID
def get_user_display_name(user_id):
    try:
        user_info = client.users_info(user=user_id)
        return user_info["user"]["profile"]["display_name"] or user_info["user"]["profile"]["real_name"]
    except SlackApiError as e:
        print(f"Error fetching user info: {e.response['error']}")
        return "Unknown User"

# Function to replace emoji labels with actual emojis
def replace_emoji_labels(text):
    # Replace Slack-specific emoji aliases first
    for alias, emoji_char in SLACK_EMOJI_MAPPING.items():
        text = text.replace(f":{alias}:", emoji_char)
    # Replace general emoji aliases
    return emoji.emojize(text)

# Function to replace user IDs and channel mentions in text with display names
def replace_user_ids_and_channels(text):
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
        headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}
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
# Function to load existing messages from a file
def load_existing_messages(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    messages = {}
    current_date = None
    for line in lines:
        if line.startswith("#### "):
            current_date = line.strip()[5:]
            messages[current_date] = []
        elif line.strip() and current_date:
            messages[current_date].append(line.strip())
    return messages

# Function to save merged messages to a file
def save_merged_messages(file_path, existing_messages, new_messages):
    if not new_messages:
        return  # Skip saving if there are no messages
    with open(file_path, "w", encoding="utf-8") as file:
        for date in sorted(new_messages.keys()):
            file.write(f"#### {date}\n\n")
            for message in new_messages[date]:
                file.write(f"{message}\n")
            file.write("\n")

# Function to fetch and save messages
def fetch_and_save_messages(channel_id, channel_name, channel_type):
    try:
        messages = []
        cursor = None
        while True:
            response = client.conversations_history(channel=channel_id, cursor=cursor, limit=200)
            messages.extend(response["messages"])
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
            time.sleep(1)  # Rate limit handling

        # Organize messages by date
        messages_by_date = {}
        for message in messages:
            timestamp = float(message.get("ts", 0))
            date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
            if date not in messages_by_date:
                messages_by_date[date] = []
            messages_by_date[date].append(message)

        # Create folders for different channel types
        folder_name = DIRECT_MSG_DIRECTORY if channel_type == "im" else GROUP_MSG_DIRECTORY if channel_type == "mpim" else CHANNEL_MSG_DIRECTORY
        os.makedirs(folder_name, exist_ok=True)

        # Replace spaces in channel_name with underscores for filename
        safe_channel_name = channel_name.replace(" ", "_")

        # File path
        file_path = os.path.join(folder_name, f"{safe_channel_name}.md")

        # Load existing messages
        existing_messages = load_existing_messages(file_path)

        # Merge new messages with existing ones (new messages take precedence)
        merged_messages = {}
        for date, date_messages in messages_by_date.items():
            merged_messages[date] = []
            for message in reversed(date_messages):  # Reverse to get chronological order
                timestamp = float(message.get("ts", 0))
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                user_display_name = get_user_display_name(message.get("user", ""))
                text = replace_emoji_labels(replace_user_ids_and_channels(message.get("text", "")))

                # Write message
                message_str = f"**{user_display_name}** ({time_str}): {text}"

                # Handle threads
                if "thread_ts" in message:
                    thread_ts = message["thread_ts"]
                    thread_messages = client.conversations_replies(channel=channel_id, ts=thread_ts)["messages"]
                    for thread_message in thread_messages[1:]:  # Skip the first message (already written)
                        thread_timestamp = float(thread_message.get("ts", 0))
                        thread_time_str = datetime.fromtimestamp(thread_timestamp).strftime("%H:%M:%S")
                        thread_user_display_name = get_user_display_name(thread_message.get("user", ""))
                        thread_text = replace_emoji_labels(replace_user_ids_and_channels(thread_message.get("text", "")))
                        message_str += f"\n    **{thread_user_display_name}** ({thread_time_str}): {thread_text}"

                # Handle reactions
                if "reactions" in message:
                    reactions = message["reactions"]
                    reaction_str = ", ".join([f"{replace_emoji_labels(f':{r['name']}:')} (x{r['count']})" for r in reactions])
                    message_str += f"\n    _Reactions_: {reaction_str}"

                ## Handle file attachments
                if BACKUP_ATTACHMENTS and "files" in message:
                    attachment_folder = os.path.join(ATTACHMENTS_DIRECTORY, safe_channel_name)
                    os.makedirs(attachment_folder, exist_ok=True)
                    image_links = []
                    for file_info in message["files"]:
                        file_url = file_info["url_private"]
                        file_name = f"{user_display_name.replace(' ', '_')}_{file_info['name']}"
                        success, final_file_path = download_file(file_url, attachment_folder, file_name)
                        if success:
                            if file_info["mimetype"].startswith("image"):
                                image_links.append(
                                    f'<img src="{os.path.relpath(final_file_path, folder_name)}" alt="{file_name}" width="200">'
                                )
                            else:
                                message_str += f"\n    [Attachment: {file_name}]({os.path.relpath(final_file_path, folder_name)})"
                        else:
                            message_str += f"\n    [Attachment: {file_name} (failed to download)]"
                    # Display images in a two-column layout using HTML
                    if image_links:
                        message_str += "\n\n<table>"
                        for i in range(0, len(image_links), 2):
                            message_str += "<tr>"
                            message_str += f"<td>{image_links[i]}</td>"
                            if i + 1 < len(image_links):
                                message_str += f"<td>{image_links[i + 1]}</td>"
                            message_str += "</tr>"
                        message_str += "</table>"

                merged_messages[date].append(message_str)

        # Save merged messages
        save_merged_messages(file_path, existing_messages, merged_messages)

        print(f"Saved {len(messages)} messages from {channel_name} to {file_path}")
    except SlackApiError as e:
        print(f"Error fetching messages from {channel_name}: {e.response['error']}")

# Fetch all channels and messages
def backup_all_messages():
    try:
        # Fetch public channels
        public_channels = client.conversations_list(types="public_channel")["channels"]
        for channel in public_channels:
            if BACKUP_LIST == ["all"] or channel["name"] in BACKUP_LIST:
                fetch_and_save_messages(channel["id"], channel["name"], "public_channel")

        # Fetch private channels
        private_channels = client.conversations_list(types="private_channel")["channels"]
        for channel in private_channels:
            if BACKUP_LIST == ["all"] or channel["name"] in BACKUP_LIST:
                fetch_and_save_messages(channel["id"], channel["name"], "private_channel")

        # Fetch multiparty direct messages (mpim)
        mpim_channels = client.conversations_list(types="mpim")["channels"]
        for channel in mpim_channels:
            if BACKUP_LIST == ["all"] or channel["name"] in BACKUP_LIST:
                fetch_and_save_messages(channel["id"], channel["name"], "mpim")

        # Fetch direct messages (im)
        im_channels = client.conversations_list(types="im")["channels"]
        for channel in im_channels:
            user_display_name = get_user_display_name(channel["user"])
            if BACKUP_LIST == ["all"] or user_display_name in BACKUP_LIST:
                fetch_and_save_messages(channel["id"], user_display_name, "im")

    except SlackApiError as e:
        print(f"Error fetching channels: {e.response['error']}")

if __name__ == "__main__":
    backup_all_messages()