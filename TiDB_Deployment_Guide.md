# MySQL/TiDB Cloud Deployment Guide

This guide walks you through setting up a free MySQL-compatible database on TiDB Cloud.
*Note: You can delete this file once the database is successfully configured.*

### 1. Account Creation
1. Go to [tidbcloud.com](https://tidbcloud.com/) and click **Sign Up Free**.
2. Sign in with Google or GitHub (no credit card required).

### 2. Create the Database Cluster
1. You will be prompted to create a cluster. Choose the **Starter** tier (Free forever).
2. For the **Region**, select the one closest to you (e.g., Singapore or Mumbai) to minimize latency.
3. Once created, you will see a popup with connection details.

### 3. Save Connection Details
In the connection details, look for the "Connect With" dropdown and select **General connection string** or **Python (PyMySQL)**.

You need to copy these 4 pieces of information:
- **Host** (e.g., `gateway01.ap-southeast-1.prod.aws.tidbcloud.com`)
- **Port** (usually `4000`)
- **User** (e.g., `2a34...root`)
- **Password** (you will be asked to generate or set a password — **save this securely!**)

### 4. Create the `marks_dashboard` schema
1. Close the connection popup and go to the cluster dashboard.
2. Click on **Chat2Query** or **SQL Editor** on the left menu.
3. Paste the following and click **Run**:
   ```sql
   CREATE DATABASE marks_dashboard;
   ```

### 5. Update Local `.env` (For testing) or Railway (For Production)
Use the copied credentials to configure your environment variables:
```env
MYSQL_HOST=your_host_address
MYSQL_PORT=4000
MYSQL_USER=your_user_string
MYSQL_PASSWORD=your_password
MYSQL_DB=marks_dashboard
```
