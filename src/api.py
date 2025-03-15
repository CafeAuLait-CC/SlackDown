import os
import time
import certifi

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackAPI:

    def __init__(self, token):

        os.environ["SSL_CERT_FILE"] = certifi.where()

        # Initialize Slack client
        self.client = WebClient(token=token)


    # Function to get user info by ID
    def get_user_display_name(self, user_id):
        try:
            user_info = self.client.users_info(user=user_id)
            return (
                user_info["user"]["profile"]["display_name"]
                or user_info["user"]["profile"]["real_name"]
            )
        except SlackApiError as e:
            print(f"Error fetching user info: {e.response['error']}")
            return "Unknown User"


    def get_conversations_list(self, type):
        try:
            return self.client.conversations_list(types=type)["channels"]
        except SlackApiError as e:
            print(f"Error fetching channels: {e.response['error']}")


    def get_conversations_history(self, channel_id, channel_name):
        try:

            messages = []
            cursor = None
            while True:
                response = self.client.conversations_history(
                    channel=channel_id, cursor=cursor, limit=200
                )
                messages.extend(response["messages"])
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
                time.sleep(1)  # Rate limit handling
            return messages
        except SlackApiError as e:
            print(f"Error fetching messages from {channel_name}: {e.response['error']}")


    def get_conversations_replies(self, channel_id, channel_name, thread_ts):
        try:
            return self.client.conversations_replies(
                                channel=channel_id, ts=thread_ts
                            )["messages"]
        except SlackApiError as e:
            print(f"Error fetching messages from {channel_name}: {e.response['error']}")


    

