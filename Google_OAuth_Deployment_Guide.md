# Google Cloud OAuth Configuration Guide (Post-Deployment)

Once your application is live on Railway, you MUST update your Google OAuth settings so that it accepts login requests from your new production domain.
*Note: You can delete this file once OAuth is working in production.*

### 1. Go to Google Cloud Console
1. Navigate to [console.cloud.google.com](https://console.cloud.google.com/).
2. Ensure you are signed into your `@vitbhopal.ac.in` account.
3. Select your `marks-dashboard` project from the top down-down menu.

### 2. Update Authorized Redirect URIs
1. Go to **APIs & Services** → **Credentials**.
2. Click on the OAuth 2.0 Client ID you created earlier to edit it.
3. Under **Authorized JavaScript origins**, click **+ ADD URI**.
   - Paste your Railway production URL (e.g., `https://marks-dashboard-production.up.railway.app`).
   - Leave `http://localhost:8000` there so local testing still works.
4. Under **Authorized redirect URIs**, click **+ ADD URI**.
   - Paste the exact same Railway URL again.
5. Click **Save** at the bottom.

*(Note: It may take up to 5-10 minutes for Google's servers to propagate the updated URIs. If you get an `Error 400: redirect_uri_mismatch` right away, just wait a few minutes and try again.)*
