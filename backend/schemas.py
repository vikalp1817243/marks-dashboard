from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class SessionCreate(BaseModel):
    name: str = Field(..., max_length=100)
    max_marks: int = Field(..., description="Either 50 or 100")
    class_size: int = Field(..., ge=10, le=200)

class SessionResponse(BaseModel):
    id: str
    name: str
    max_marks: int
    class_size: int
    created_at: datetime
    expires_at: datetime
    spots_remaining: int
    submission_url: str
    dashboard_url: str

class ScoreSubmit(BaseModel):
    score: float = Field(..., ge=0)

class CachedStatsResponse(BaseModel):
    session_id: str
    mean: Optional[float]
    median: Optional[float]
    mode: Optional[float]
    std_dev: Optional[float]
    min: Optional[float]
    max: Optional[float]
    q1: Optional[float]
    q3: Optional[float]
    count: int
    interpretation: Optional[str]
    histogram_json: Optional[str]
    updated_at: datetime
