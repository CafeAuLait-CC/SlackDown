**Create a Slack App**:
   - Go to the [Slack API](https://api.slack.com/apps) and create a new app. See [this instruction](SlackAppSetup.md) for more details.
   - Add the following OAuth scopes to your app:
     - `channels:history`
     - `groups:history`
     - `im:history`
     - `mpim:history`
     - `users:read`
     - `files:read`
   - Install the app to your workspace and obtain the **User OAuth Token**.