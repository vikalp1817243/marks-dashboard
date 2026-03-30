# Marks Dashboard

An anonymous, peer-driven web application for analyzing class performance at **VIT Bhopal**. Any student can create an exam session, share a link with classmates, and everyone submits their marks anonymously. A real-time statistical dashboard is generated instantly.

**All data is automatically deleted after 24 hours.**

## Features

- **Relative Grading (Bell Curve System)** - Dynamically generates a standard normal distribution curve for 100-mark exams based on the VIT grading algorithm, charting clear thresholds for letter grades.
- **Interactive Scatter Plots** - Plots each student's exact score as a raw data point directly on the probability density curve to visualize their exact standing in the class.
- **Session Deduplication** - Generates unique session hashes using Class ID, Faculty Name, Slot, and Course Code to prevent duplicate databases for the same class module.
- **Strict Data Validation** - Rigid numerical validation bounds on the client and server to prevent database corruption from malformed entries.
- **100% Anonymous** - Marks and identities are stored in separate, unlinked database tables.
- **Real-time Dashboard** - WebSocket-powered live updates as marks come in.
- **Full Statistical Analysis** - Mean, Median, Mode, Standard Deviation, Quartiles, Histograms.
- **AI Interpretation** - Automatic text analysis of class performance.
- **24h Auto-Delete** - All session data is purged automatically.
- **Push Notifications** - Browser push alerts when 90% capacity is reached.
- **Google SSO** - Only `@vitbhopal.ac.in` accounts can participate.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.10+) |
| Database | MySQL + SQLAlchemy (Async) |
| Stats Engine | NumPy |
| Auth | Google OAuth 2.0 (OpenID Connect) |
| Frontend | Vanilla HTML/JS + Chart.js |
| Real-time | WebSocket |
| Notifications | Web Push (pywebpush + VAPID) |

## Quick Start

### 1. Clone & Setup

```bash
cd marksDashboard

# Create virtual environment in root (IDE auto-detects it here)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. MySQL Database

```bash
mysql -u root -p
```

```sql
CREATE DATABASE marks_dashboard;
```

### 3. Environment Variables

```bash
cp .env.example .env
# Edit .env with your MySQL credentials and Google Client ID
```

### 4. Run the Server

```bash
source .venv/bin/activate
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit: [http://localhost:8000](http://localhost:8000)

## Google Cloud OAuth Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project → `marks-dashboard`
3. APIs & Services → OAuth consent screen → External
4. Credentials → Create OAuth 2.0 Client ID
5. Set authorized origins to `http://localhost:8000`
6. Copy Client ID to `.env`

## License

MIT
