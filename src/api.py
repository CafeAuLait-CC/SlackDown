import os
import certifi

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackAPI:
    def __init__(self, token):
        os.environ["SSL_CERT_FILE"] = certifi.where()
        self.client = WebClient(token=token)

    def get_user_info(self, user_id):
        try:
            user_info = self.client.users_info(user=user_id)
            return (
                user_info["user"]["profile"]["display_name"]
                or user_info["user"]["profile"]["real_name"]
            )
        except SlackApiError as e:
            print(f"Error fetching user info: {e.response['error']}")
            return "Unknown User"

    def get_conversations_history(self, channel_id, cursor=None, limit=200):
        try:
            response = self.client.conversations_history(
                channel=channel_id, cursor=cursor, limit=limit
            )
            return response["messages"], response.get("response_metadata", {}).get(
                "next_cursor"
            )
        except SlackApiError as e:
            print(f"Error fetching messages: {e.response['error']}")
            return [], None

    def get_conversations_replies(self, channel_id, thread_ts):
        try:
            response = self.client.conversations_replies(
                channel=channel_id, ts=thread_ts
            )
            return response["messages"]
        except SlackApiError as e:
            print(f"Error fetching thread replies: {e.response['error']}")
            return []
