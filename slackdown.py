from src.api import SlackAPI
from src.config import load_config
from src.message_processor import fetch_and_save_messages


# Fetch all channels and messages
def backup_all_messages(config):
    slack = SlackAPI(config["slack_token"])

    slack.test_token()

    # Fetch public channels
    public_channels = slack.get_conversations_list(type="public_channel")
    for channel in public_channels:
        if config["backup_list"] == ["all"] or channel["name"] in config["backup_list"]:
            fetch_and_save_messages(channel["id"], channel["name"], "public_channel")

    # Fetch private channels
    private_channels = slack.get_conversations_list(type="private_channel")
    for channel in private_channels:
        if config["backup_list"] == ["all"] or channel["name"] in config["backup_list"]:
            fetch_and_save_messages(channel["id"], channel["name"], "private_channel")

    # Fetch multiparty direct messages (mpim)
    mpim_channels = slack.get_conversations_list(type="mpim")
    for channel in mpim_channels:
        if config["backup_list"] == ["all"] or channel["name"] in config["backup_list"]:
            fetch_and_save_messages(channel["id"], channel["name"], "mpim")

    # Fetch direct messages (im)
    im_channels = slack.get_conversations_list(type="im")
    for channel in im_channels:
        user_display_name = slack.get_user_display_name(channel["user"])
        if (
            config["backup_list"] == ["all"]
            or user_display_name in config["backup_list"]
        ):
            fetch_and_save_messages(channel["id"], user_display_name, "im")


if __name__ == "__main__":
    config = load_config()
    backup_all_messages(config)
