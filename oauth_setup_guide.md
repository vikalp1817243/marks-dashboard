# Google Cloud OAuth Setup Guide

**IMPORTANT: Billing Safety**
Using Google Cloud OAuth 2.0 for authentication is **completely free** and does not consume any paid quota. To absolutely guarantee you are never charged:
- **Do not link a credit card** or create a Billing Account for this specific project.
- If Google Cloud prompts you to start a free trial or enable billing, you can safely skip/ignore it for OAuth purposes. Without a linked billing account, it is physically impossible for Google to charge you.

---

### Step 1: Sign In & Create a Project
1. Go to [console.cloud.google.com](https://console.cloud.google.com/).
2. Sign in using your educational email account (`@vitbhopal.ac.in`).
3. In the top navigation bar, click on **Select a project** (or your current project name), then click **New Project** in the popup window.
4. Set the **Project Name** to `marks-dashboard`.
5. Leave Location as is, and click **Create**. Wait a few seconds for the project to be created, and make sure it is actively selected.

### Step 2: Configure the App Branding & Audience (New Google UI)
1. From the left-hand menu, navigate to **APIs & Services** → **OAuth consent screen** (or **Google Auth Platform**).
2. Click the blue **Get started** button in the center of the screen.
3. Under **App Information** (Branding), fill in:
   - **App name**: `Marks Dashboard`
   - **User support email**: Select your `@vitbhopal.ac.in` email from the dropdown.
4. Click **Next** to go to **Audience**.
5. Select **Internal** (Since you only wantVIT Bhopal students for now. This also bypasses Google's strict verification process! You can always change this to External later).
6. Click **Next** to go to **Contact Information**, enter your `@vitbhopal.ac.in` email, and click **Create** / **Finish**.

### Step 3: Create OAuth Credentials
1. Still under **APIs & Services**, click on **Credentials** from the left-side menu.
2. Click the **+ CREATE CREDENTIALS** button at the top and select **OAuth 2.0 Client ID**.
3. For the **Application type**, select **Web application**.
4. In the **Name** field, you can leave it as "Web client 1" or name it "Marks Dashboard Client".
5. Under **Authorized JavaScript origins**:
   - Click **+ ADD URI**
   - Paste: `http://localhost:8000`
6. Under **Authorized redirect URIs**:
   - Click **+ ADD URI**
   - Paste: `http://localhost:8000`
7. Click **Create**.

### Step 4: Add to Your Application
1. A modal will pop up with your newly generated credentials.
2. Copy the **Client ID**.
3. Open the `.env` file in your `marksDashboard` project folder.
4. Paste the Client ID into your environment variables. 
   *(For example: `VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com` or whatever variable name your app expects)*.
