import os
import emoji

from datetime import datetime
from src.api import SlackAPI
from src.config import load_config
from src.helper import calculate_url_hash, download_file


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
    "tada": "🎉",
    "scream_cat": "🙀",
    "pensive": "😔",
    "smiling_face_with_3_hearts": "🥰",
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

    # Preserve original line structure
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        # Preserve leading whitespace for indentation
        leading_whitespace = len(line) - len(line.lstrip())
        indent = ' ' * leading_whitespace
        
        words = line.strip().split()
        for i, word in enumerate(words):
            if word.startswith("<@") and word.endswith(">"):
                user_id = word[2:-1]
                display_name = slack.get_user_display_name(user_id)
                words[i] = f"`@{display_name}`"
            elif word == "<!channel>":
                words[i] = "`@channel`"
        
        # Reconstruct line with original indentation
        processed_line = indent + ' '.join(words)
        processed_lines.append(processed_line)
    
    return '\n'.join(processed_lines)


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
        sorted_new_dates = sorted(new_messages.keys())
        # Write old records first
        for date in sorted(existing_messages.keys()):
            if date >= sorted_new_dates[0]: # if overlapping with new records
                continue
            file.write(f"#### {date}\n")
            for message in existing_messages[date]:
                file.write(f"{message}\n")
            file.write("\n")
        # Write new records
        for date in sorted_new_dates:
            file.write(f"#### {date}\n")
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

            # Detect and format code blocks
            if '```' in text:
                # Split into code blocks and regular text
                parts = text.split('```')
                formatted_parts = []
                in_code_block = False
                
                for part in parts:
                    if in_code_block:
                        formatted_parts.append(f"```\n{part.strip()}\n```")
                    else:
                        formatted_parts.append(part)
                    in_code_block = not in_code_block
                
                text = '\n'.join(formatted_parts)

            # Write message
            message_str = f"\n**{user_display_name}** ({time_str}):\n{text}"

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
            if config["backup_attachments"]:
                if "files" in message:
                    attachment_folder = os.path.join(
                        config["attachments_dir"], safe_channel_name
                    )
                    os.makedirs(attachment_folder, exist_ok=True)
                    image_links = []
                    
                    for file_info in message["files"]:
                        # Handle expired files first
                        if file_info.get('mode') == 'hidden_by_limit':
                            file_id = file_info['id']
                            # Search for existing files with this ID pattern: {file_id}_*
                            existing_files = [f for f in os.listdir(attachment_folder) 
                                            if f.startswith(f"{file_id}_")]
                            
                            if existing_files:
                                # Find most recent version using timestamp suffix
                                sorted_files = sorted(existing_files, 
                                                    key=lambda x: x.split('-')[-1].split('.')[0], 
                                                    reverse=True)
                                archived_file = sorted_files[0]
                                
                                # Extract original name from filename pattern: {id}_{user}_{name}
                                try:
                                    original_name = '_'.join(archived_file.split('_')[2:])
                                    original_name = original_name.rsplit('-', 1)[0]  # Remove timestamp
                                except:
                                    original_name = "archived_file"
                                    
                                archived_file_path = os.path.join(attachment_folder, archived_file)
                                message_str += f"\n    [Attachment: {original_name}]({os.path.relpath(archived_file_path, folder_name)})"
                                
                                # Handle images
                                if archived_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                    img_tag = f'<img src="{os.path.relpath(archived_file_path, folder_name)}" alt="{original_name}" width="200">'
                                    image_links.append(img_tag)
                            else:
                                message_str += f"\n    [Attachment: Expired file (no local copy available, id={file_id})]"
                            continue

                        # Handle active files
                        try:
                            file_url = file_info["url_private"]
                            file_id = file_info["id"]
                            original_name = file_info["name"]
                            user_part = user_display_name.replace(' ', '_')
                            
                            # Generate filename pattern: {file_id}_{user}_{name}-{timestamp}.ext
                            base_name, file_ext = os.path.splitext(original_name)
                            clean_base = base_name.replace(' ', '_').replace('\u202f', '_')
                            timestamp_str = datetime.now().strftime('%Y%m%d%H%M%S')
                            
                            # Construct temp filename with timestamp before extension
                            temp_filename = f"{file_id}_{user_part}_{clean_base}-{timestamp_str}{file_ext}"
                            
                            # Check for existing file FIRST
                            final_filename = f"{file_id}_{user_part}_{clean_base}{file_ext}"
                            final_path = os.path.join(attachment_folder, final_filename)

                            if not os.path.exists(final_path):
                                # Download only if needed
                                temp_filename = f"{file_id}_{user_part}_{clean_base}-{timestamp_str}{file_ext}"
                                success, temp_path = download_file(file_url, attachment_folder, temp_filename)
                                
                                if success:
                                    os.rename(temp_path, final_path)  # Safe atomic operation
                                    # message_str += f"\n    [Attachment: {clean_base}{file_ext}]"
                                else:
                                    message_str += f"\n    [Attachment: {clean_base}{file_ext} (download failed)]"

                            # Handle display
                            if file_info["mimetype"].startswith("image"):
                                img_tag = f'<img src="{os.path.relpath(final_path, folder_name)}" alt="{clean_base}{file_ext}" width="200">'
                                image_links.append(img_tag)
                            else:
                                message_str += f"\n    [Attachment: {clean_base}{file_ext}]({os.path.relpath(final_path, folder_name)})"
                            
                        except KeyError:
                            message_str += "\n    [Attachment: Invalid file data]"

                    # Display images in a two-column layout using HTML
                    if image_links:
                        message_str += "\n<table>"
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
                
                if "attachments" in message:
                    attachment_folder = os.path.join(config["attachments_dir"], safe_channel_name)
                    image_links = []
                    
                    for attachment in message["attachments"]:
                        if "blocks" in attachment:
                            for block in attachment["blocks"]:
                                if block["type"] == "image":
                                    image_url = block.get("image_url")
                                    if image_url:
                                        # Similar download logic as files
                                        try:
                                            # Generate filename from URL
                                            file_id = calculate_url_hash(image_url.encode())
                                            user_part = user_display_name.replace(' ', '_')
                                            original_name = os.path.basename(image_url).split('?')[0]
                                            base_name, file_ext = os.path.splitext(original_name)
                                            
                                            # Download and process
                                            final_filename = f"{file_id}_{user_part}_{base_name}{file_ext}"
                                            final_path = os.path.join(attachment_folder, final_filename)
                                            
                                            if not os.path.exists(final_path):
                                                success, temp_path = download_file(image_url, attachment_folder, final_filename)
                                                if not success:
                                                    continue
                                                os.rename(temp_path, final_path)
                                            
                                            # Add image to message
                                            img_tag = f'<img src="{os.path.relpath(final_path, folder_name)}" width="200">'
                                            image_links.append(img_tag)
                                        except Exception as e:
                                            message_str += f"\n    [GIF download failed: {str(e)}]"
                    
                    # Add image grid
                    if image_links:
                        message_str += "\n<table>"
                        for i in range(0, len(image_links), 2):
                            message_str += "<tr>"
                            message_str += f"<td>{image_links[i]}</td>"
                            if i+1 < len(image_links):
                                message_str += f"<td>{image_links[i+1]}</td>"
                            message_str += "</tr>"
                        message_str += "</table>"

            merged_messages[date].append(message_str)

    # Save merged messages
    save_merged_messages(file_path, existing_messages, merged_messages)

    print(f"Saved {len(messages)} messages from {channel_name} to {file_path}")
