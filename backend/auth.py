import hashlib
import re
import asyncio
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests
import base64

from config import GOOGLE_CLIENT_ID, SECRET_SALT, ALLOWED_DOMAIN, EMAIL_REGEX

security = HTTPBearer()

def hash_email(email: str, session_id: str) -> str:
    """Hash the email using SHA-256 and a secret salt + session ID to ensure anonymity."""
    payload = f"{email}:{SECRET_SALT}:{session_id}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def encrypt_email(email: str) -> str:
    """MVP: Base64 encoding for simplicity.
    In production, use Fernet symmetric encryption."""
    return base64.b64encode(email.encode('utf-8')).decode('utf-8')

def decrypt_email(encrypted: str) -> str:
    return base64.b64decode(encrypted.encode('utf-8')).decode('utf-8')

def _verify_token_sync(token: str) -> dict:
    """Synchronous Google token verification (runs in a thread pool).
    
    The google-auth library internally uses the synchronous `requests` lib
    to fetch Google's public certificates. Running this in the main async
    event loop would block ALL other requests. By isolating it in a thread,
    the event loop remains free to process other I/O-bound work.
    """
    return id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

async def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify the Google JWT, check domain, and return the email.
    
    Fix #3: The actual token verification is offloaded to a thread via
    asyncio.to_thread() so it does not block the async event loop.
    """
    token = credentials.credentials
    if GOOGLE_CLIENT_ID == "mock-client-id":
        # Dev bypass if actual auth isn't set up yet.
        # Format for mock token: "mock_token:user.24bcy12345@vitbhopal.ac.in"
        if token.startswith("mock_token:"):
            email = token.split(":")[1]
        else:
            email = "test.24bcy12345@vitbhopal.ac.in"
    else:
        try:
            # Fix #3: Run blocking HTTP call in a separate thread
            idinfo = await asyncio.to_thread(_verify_token_sync, token)
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
                
            hd = idinfo.get('hd')
            if hd != ALLOWED_DOMAIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Only {ALLOWED_DOMAIN} accounts are allowed."
                )
                
            email = idinfo.get('email', '')
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google ID token"
            )

    # Validate email regex
    if not re.match(EMAIL_REGEX, email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email format does not match required VIT Bhopal student format (e.g. jay.24bcy10278@vitbhopal.ac.in)"
        )
        
    return email
