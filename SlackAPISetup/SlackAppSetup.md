Step by step instruction on how to obtain the **User OAuth Token**.

**Create a Slack App**:
1. Go to the [Slack API](https://api.slack.com/) website and click "**Your apps**" in the top right corner. If you are not signed in, it will ask you to _sign in into your Slack account_.
	   ![0. api_page](images/0.api_page.png)
	   
   
2. After signing in, select the workspace you want to login.
	   ![1. login](images/1.login.png)

3. The website probably will not redirect you the the API page, but brings you to the Slack chat page. So you need to type the URL in the address bar again: [https://api.slack.com/apps](https://api.slack.com/apps). **Do not type the address until you see this page**:
	   ![2. after_login](images/2.after_login.png)

4. Then click the **Create an App** button to create a new app. 
	   ![3. new_app](images/3.new_app.png)
	   
   
5. In the prompt dialog, select **From scratch**:

	 ![4. scratch](images/4.scratch.png)
   
6. Create an app name, and select your workspace. (It's recommended to use your name/alias as the prefix/suffix of the app name) You can always change it later, so no need to hesitate
	   ![5. app_name](images/5.app_name.png)

7. Clicking **Create App**, you will see the information page of your Slack app. Select **OAuth & Permissions** on the left side:
	![6. info](images/6.info.png)

8. Scroll down to the **Scopes** section, in the **User Token Scopes** part, Add the following OAuth scopes to your app:
     - `channels:history`
     - `channels:read`
     - `groups:history`
     - `groups:read`
     - `im:history`
     - `im:read`
     - `mpim:history`
     - `mpim:read`
     - `users:read`
     - `files:read`
 
	![7. user_token_scope](images/7.user_token_scope.png)
	**IMPORTANT**: Make sure you add the scopes in the `User Token Scopes`, `Bot Token Scopes` won't work!
	![8. add_scopes](images/8.add_scopes.png)
9. Scroll up, find the **Install** button and install the app to your workspace
	![9. install](images/9.install.png)
10. After installing the app to your workspace, you will see the **User OAuth Token**, copy it into the `config.txt` file in this project source code, and you are good to go!
	![10. user_token](images/10.user_token.png)