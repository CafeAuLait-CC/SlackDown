Step by step instruction on how to obtain the **User OAuth Token**.

**Create a Slack App**:
1. Go to the [Slack API](https://api.slack.com/) website and click "**Your apps**" in the top right corner. If you are not signed in, it will ask you to _sign in into your Slack account_.
	  
   <img src="images/0.api_page.png" alt="drawing" width="600"/>
	   
   
3. After signing in, select the workspace you want to login.
	  
   <img src="images/1.login.png" alt="drawing" width="600"/>

4. The website probably will not redirect you the the API page, but brings you to the Slack chat page. So you need to type the URL in the address bar again: [https://api.slack.com/apps](https://api.slack.com/apps). **Do not type the address until you see this page**:
	   
   <img src="images/2.after_login.png" alt="drawing" width="600"/>

5. Then click the **Create an App** button to create a new app. 
	   
   <img src="images/3.new_app.png" alt="drawing" width="600"/>
	   
   
6. In the prompt dialog, select **From scratch**:
	
   <img src="images/4.scratch.png" alt="drawing" width="600"/>
   
7. Create an app name, and select your workspace. (It's recommended to use your name/alias as the prefix/suffix of the app name) You can always change it later, so no need to hesitate.
    
   <img src="images/5.app_name.png" alt="drawing" width="600"/>

8. Clicking **Create App**, you will see the information page of your Slack app. Select **OAuth & Permissions** on the left side:
	
   <img src="images/6.info.png" alt="drawing" width="600"/>

15. Scroll down to the **Scopes** section, in the **User Token Scopes** part, Add the following OAuth scopes to your app:
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
 
   <img src="images/7.user_token_scope.png" alt="drawing" width="600"/>

**IMPORTANT**: Make sure you add the scopes in the `User Token Scopes`, `Bot Token Scopes` won't work!
   
   <img src="images/8.add_scopes.png" alt="drawing" width="600"/>
   
9. Scroll up, find the **Install** button and install the app to your workspace
    
   <img src="images/9.install.png" alt="drawing" width="600"/>
   
10. After installing the app to your workspace, you will see the **User OAuth Token**, copy it into the `config.txt` file in this project source code, and **you are good to go**!
	
   <img src="images/10.user_token.png" alt="drawing" width="600"/>
   
