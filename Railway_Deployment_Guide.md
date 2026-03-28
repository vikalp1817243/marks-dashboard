# Railway.app Backend Deployment Guide

This guide walks you through deploying the Python FastAPI backend on Railway.app.
*Note: You can delete this file once the backend is successfully deployed.*

### 1. Prepare GitHub Repository
Ensure all code from your local machine has been committed and pushed to your GitHub repository.

### 2. Create Railway Account
1. Go to [railway.app](https://railway.app/) and sign in with GitHub.
2. Accept the terms. You will automatically receive the $1/month free tier credits.

### 3. Deploy the Service
1. On the Railway dashboard, click **+ New Project**.
2. Select **Deploy from GitHub repo**.
3. Select your `marksDashboard` repository.
4. Click **Deploy Now**.
*(It will start building, but it might fail initially because it missing environment variables. That is normal.)*

### 4. Configure Environment Variables
1. Click on your newly created service box in the Railway dashboard.
2. Go to the **Variables** tab.
3. Click **New Variable** and add the following from your local `.env`:
   - `GOOGLE_CLIENT_ID`
   - `SECRET_SALT`
   - `MYSQL_HOST` (From TiDB)
   - `MYSQL_PORT` (From TiDB, likely `4000`)
   - `MYSQL_USER` (From TiDB)
   - `MYSQL_PASSWORD` (From TiDB)
   - `MYSQL_DB` (Set to `marks_dashboard`)
   - `VAPID_PUBLIC_KEY`
   - `VAPID_PRIVATE_KEY`
   - `VAPID_CLAIM_EMAIL`
   
### 5. Add Custom Domain / Production URL
1. Go to the **Settings** tab of your service.
2. Under "Networking", click **Generate Domain**.
3. Railway will give you a public URL (e.g., `https://marks-dashboard-production.up.railway.app`).
**Copy this URL**.

### 6. Set BASE_URL Variable
1. Go back to the **Variables** tab.
2. Add a new variable:
   - `BASE_URL` = `https://marks-dashboard-production.up.railway.app` (The exact URL copied in step 5, with no trailing slash).

Railway will instantly restart your application with the final configuration.
