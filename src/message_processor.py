import os
import emoji

from datetime import datetime
from src.api import SlackAPI
from src.config import load_config
from src.helper import download_file


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


# Function to replace emoji labels with actual emojis
def replace_emoji_labels(text):
    # Replace Slack-specific emoji aliases first
    for alias, emoji_char in SLACK_EMOJI_MAPPING.items():
        text = text.replace(f":{alias}:", emoji_char)
    # Replace general emoji aliases
    return emoji.emojize(text)


# Function to replace user IDs and channel mentions in text with display names
def replace_user_ids_and_channels(slack, text):
    if not text:
        return text
    words = text.split()
    for i, word in enumerate(words):
        if word.startswith("<@") and word.endswith(">"):
            user_id = word[2:-1]
            display_name = slack.get_user_display_name(user_id)
            words[i] = f"`@{display_name}`"
        elif word == "<!channel>":
            words[i] = "`@channel`"
    return " ".join(words)


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
    config = load_config()
    slack = SlackAPI(config["slack_token"])

    print(f"Saving {channel_name}...", end="\r")

    messages = slack.get_conversations_history(channel_id, channel_name)

    # Organize messages by date
    messages_by_date = {}
    for message in messages:
        timestamp = float(message.get("ts", 0))
        date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
        if date not in messages_by_date:
            messages_by_date[date] = []
        messages_by_date[date].append(message)

    # Create folders for different channel types
    folder_name = (
        config["direct_msg_dir"]
        if channel_type == "im"
        else config["group_msg_dir"]
        if channel_type == "mpim"
        else config["channel_msg_dir"]
    )
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
            user_display_name = slack.get_user_display_name(message.get("user", ""))
            text = replace_emoji_labels(
                replace_user_ids_and_channels(slack, message.get("text", ""))
            )

            # Write message
            message_str = f"**{user_display_name}** ({time_str}): {text}"

            # Handle threads
            if "thread_ts" in message:
                thread_ts = message["thread_ts"]
                thread_messages = slack.get_conversations_replies(
                    channel_id, channel_name, thread_ts
                )
                for thread_message in thread_messages[
                    1:
                ]:  # Skip the first message (already written)
                    thread_timestamp = float(thread_message.get("ts", 0))
                    thread_time_str = datetime.fromtimestamp(thread_timestamp).strftime(
                        "%H:%M:%S"
                    )
                    thread_user_display_name = slack.get_user_display_name(
                        thread_message.get("user", "")
                    )
                    thread_text = replace_emoji_labels(
                        replace_user_ids_and_channels(
                            slack, thread_message.get("text", "")
                        )
                    )
                    message_str += f"\n    **{thread_user_display_name}** ({thread_time_str}): {thread_text}"

            # Handle reactions
            if "reactions" in message:
                reactions = message["reactions"]
                reaction_list = []
                for r in reactions:
                    emoji_label = replace_emoji_labels(f":{r['name']}:")
                    reaction_list.append(f"{emoji_label} (x{r['count']})")
                reaction_str = ", ".join(reaction_list)
                message_str += f"\n    _Reactions_: {reaction_str}"

            ## Handle file attachments
            if config["backup_attachments"] and "files" in message:
                attachment_folder = os.path.join(
                    config["attachments_dir"], safe_channel_name
                )
                os.makedirs(attachment_folder, exist_ok=True)
                image_links = []
                for file_info in message["files"]:
                    file_url = file_info["url_private"]
                    file_name = (
                        (f"{user_display_name}_{file_info['name']}")
                        .replace(" ", "_")
                        .replace("\u202f", "_")
                        # '\u202F' is a narrow no-break space (U+202F)
                    )
                    success, final_file_path = download_file(
                        file_url, attachment_folder, file_name
                    )
                    if success:
                        if file_info["mimetype"].startswith("image"):
                            image_links.append(
                                f'<img src="{os.path.relpath(final_file_path, folder_name)}" alt="{file_name}" width="200">'
                            )
                        else:
                            message_str += f"\n    [Attachment: {file_name}]({os.path.relpath(final_file_path, folder_name)})"
                    else:
                        message_str += (
                            f"\n    [Attachment: {file_name} (failed to download)]"
                        )
                # Display images in a two-column layout using HTML
                if image_links:
                    message_str += "\n\n<table>"
                    for i in range(0, len(image_links), 2):
                        message_str += "<tr>"
                        # Force to use forward slashes '/'' on Windows for Markdown to display images properly
                        forward_slash_path = image_links[i].replace("\\", "/")
                        message_str += f"<td>{forward_slash_path}</td>"
                        if i + 1 < len(image_links):
                            forward_slash_path = image_links[i + 1].replace("\\", "/")
                            message_str += f"<td>{forward_slash_path}</td>"
                        message_str += "</tr>"
                    message_str += "</table>"

            merged_messages[date].append(message_str)

    # Save merged messages
    save_merged_messages(file_path, existing_messages, merged_messages)

    print(f"Saved {len(messages)} messages from {channel_name} to {file_path}")
