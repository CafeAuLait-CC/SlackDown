import configparser



def load_config():

    # Load configuration from config.txt
    config = configparser.ConfigParser()
    config.read("config.txt")

    return {
        # Slack token
        "slack_token": config.get("Slack", "User_OAuth_Token"),

        # Directories
        "direct_msg_dir": config.get("Directories", "Direct_Msg_Directory", fallback="dm"),
        "group_msg_dir": config.get("Directories", "Group_Msg_Directory", fallback="groups"),
        "channel_msg_dir": config.get("Directories", "Channel_Msg_Directory", fallback="channels"),
        "attachments_dir": config.get("Directories", "Attachment_Directory", fallback="attachments"),

        # Backup options
        "backup_attachments": config.getboolean("Options", "Backup_Attachments", fallback=True),
        "backup_list": config.get("Options", "Backup_List", fallback="all").split(","),
    }