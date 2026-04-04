import os
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

# Prefer .env.local for local development; fall back to .env for production
_env_local = Path(__file__).parent / ".env.local"
if _env_local.exists():
    load_dotenv(_env_local)
else:
    load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "mock-client-id")
SECRET_SALT = os.getenv("SECRET_SALT", "default-secret-salt-for-dev")

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "marks_dashboard")

DATABASE_URL = f"mysql+aiomysql://{urllib.parse.quote_plus(MYSQL_USER)}:{urllib.parse.quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# TiDB requires SSL connection. We apply it if the host is a TiDB host.
import ssl
ssl_ctx = ssl.create_default_context()
CONNECT_ARGS = {"ssl": ssl_ctx} if "tidbcloud" in MYSQL_HOST else {}

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL", "mailto:noreply@marksdashboard.app")

ALLOWED_DOMAIN = "vitbhopal.ac.in"
EMAIL_REGEX = r"^[a-z]+\.\d{2}[a-z]{3}\d{5}@vitbhopal\.ac\.in$"
