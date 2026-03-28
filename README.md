# 📊 Marks Dashboard

An anonymous, peer-driven web application for analyzing class performance at **VIT Bhopal**. Any student can create an exam session, share a link with classmates, and everyone submits their marks anonymously. A real-time statistical dashboard is generated instantly.

**All data is automatically deleted after 24 hours.**

## Features

- 🔒 **100% Anonymous** — Marks and identities are stored in separate, unlinked database tables
- 📈 **Real-time Dashboard** — WebSocket-powered live updates as marks come in
- 📊 **Full Statistical Analysis** — Mean, Median, Mode, Standard Deviation, Quartiles, Histograms
- 🤖 **AI Interpretation** — Automatic text analysis of class performance
- ⏳ **24h Auto-Delete** — All session data is purged automatically
- 🔔 **Push Notifications** — Browser push alerts when 90% capacity is reached
- 🔐 **Google SSO** — Only `@vitbhopal.ac.in` accounts can participate

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

## Architecture

```
Student A creates session → Shares link → Students B,C,D submit marks
                                            ↓
                                    [Google SSO Verification]
                                            ↓
                                    [SHA-256 Hash Email] ──→ Submission Table (hash only)
                                            ↓
                                    [Score Only] ──→ ExamScore Table (no identity)
                                            ↓
                                    [NumPy Stats Engine] → CachedStats → WebSocket → Dashboard
```

## License

MIT
