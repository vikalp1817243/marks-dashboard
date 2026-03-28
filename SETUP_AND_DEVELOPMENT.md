# Marks Dashboard: Setup & Development Guide

Welcome to the Marks Dashboard project! This document outlines everything you need to know from configuring Google Cloud authentication to running the project on your local machine.

---

## 1. Google Cloud OAuth Setup (One-Time)

To allow users to log in securely using their `@vitbhopal.ac.in` email, you need to spin up a Google Cloud Project and obtain a Client ID.

> **⚠️ Billing Safety Warning**
> OAuth login is 100% free. To ensure you are never charged for anything in Google Cloud, **do not attach a credit card** or create a Billing Account for this project.

### Step 1.1: Create the Project
1. Go to [console.cloud.google.com](https://console.cloud.google.com/).
2. Sign in with your educational email (`@vitbhopal.ac.in`).
3. Click the Project Dropdown at the top left → **New Project**.
4. Name the project `marks-dashboard` and click **Create**. Ensure it is selected.

### Step 1.2: Configure App Branding (New UI)
1. Navigate to **APIs & Services** → **OAuth consent screen** (or Google Auth Platform).
2. Click the blue **Get started** button.
3. Under **App Information**, enter `Marks Dashboard` as the App name and select your email for the support email. Click **Next**.
4. Under **Audience**, select **Internal** (this restricts logins to only individuals with `@vitbhopal.ac.in` emails and skips Google's strict app verification process!). Click **Next**.
5. Under **Contact Information**, enter your email again and click **Finish/Create**.

### Step 1.3: Generate the Client ID
1. In the Google Auth Platform, you should now see a button that says **Create OAuth client** (or click **Clients** on the left menu, then **+ CREATE CLIENT**).
2. For **Application type**, select **Web application**.
3. Scroll to **Authorized JavaScript origins** → click **+ ADD URI** → paste `http://localhost:8000`.
4. Scroll to **Authorized redirect URIs** → click **+ ADD URI** → paste `http://localhost:8000`.
5. Click **Create**.
6. A popup will appear. **Copy your Client ID** (you can ignore the Client Secret for most basic frontend setups).

---

## 2. Local Development Environment

### Prerequisites
Make sure you have the following installed on your machine:
- **Node.js** (if you use JavaScript for the backend/frontend tooling)
- **Python** (if the backend is written in Python/FastAPI/Django)
- A modern web browser (Chrome, Edge, Firefox)

### Step 2.1: Configuring Environment Variables
1. Open the project folder (`marksDashboard`) in your code editor.
2. In the `frontend` directory, look for (or create) a `.env` file or configuration file where API keys are stored.
3. Add your recently copied Google Client ID:
   ```env
   GOOGLE_CLIENT_ID=your-copied-client-id-here.apps.googleusercontent.com
   ```
   *(Note: Depending on how the frontend is built, this might need to go into a specific `.js` config file or be prefixed with `VITE_` or `REACT_APP_` if using a framework).*

### Step 2.2: Running the Frontend
The frontend consists of HTML and JavaScript files (like `submit.html` and `dashboard.html`).
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. You can serve these files using a simple local server. For example:
   - Using Python:
     ```bash
     python3 -m http.server 8000
     ```
   - Using a Node package like `serve` or `live-server`:
     ```bash
     npx serve -p 8000
     ```
3. Open your browser and navigate to `http://localhost:8000`.

### Step 2.3: Running the Backend
*(Detailed instructions will be added here once the backend framework is finalized. Typical steps involve creating a virtual environment, installing dependencies, and running the server).*
1. Navigate to the backend folder:
   ```bash
   cd ../backend
   ```
2. Install dependencies (e.g., `pip install -r requirements.txt` or `npm install`).
3. Start the server on its designated port and ensure the frontend is configured to communicate with it.

---

## 3. Contributing & Code Structure

- `/frontend`: Contains all the HTML, CSS, and Vanilla JS logic (`submit.html`, `dashboard.js`, etc.). Keep the logic modular and separate DOM manipulation from API calls.
- `/backend`: Contains the server logic, database models, and API endpoints.

*This guide is a living document and will be updated as the project evolves!*
