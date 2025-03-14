import configparser
from src.api import SlackAPI
from src.helpers import replace_emoji_labels, replace_user_ids_and_channels
from src.utils import download_file


# Load configuration
config = configparser.ConfigParser()
config.read("config.txt")
SLACK_TOKEN = config.get("Slack", "User_OAuth_Token")

# Initialize Slack API
slack_api = SlackAPI(SLACK_TOKEN)

# Fetch all channels and messages
def backup_all_messages():
    try:
        # Fetch public channels
        public_channels = client.conversations_list(types="public_channel")["channels"]
        for channel in public_channels:
            if BACKUP_LIST == ["all"] or channel["name"] in BACKUP_LIST:
                fetch_and_save_messages(
                    channel["id"], channel["name"], "public_channel"
                )

        # Fetch private channels
        private_channels = client.conversations_list(types="private_channel")[
            "channels"
        ]
        for channel in private_channels:
            if BACKUP_LIST == ["all"] or channel["name"] in BACKUP_LIST:
                fetch_and_save_messages(
                    channel["id"], channel["name"], "private_channel"
                )

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

