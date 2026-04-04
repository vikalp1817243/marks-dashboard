from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class SessionCreate(BaseModel):
    exam_type: str = Field(..., description="E.g., Mid-Term (50), Term-End (100), Overall (100)")
    class_id: Optional[str] = Field(None, description="Optional class ID")
    faculty_name: str = Field(..., description="Faculty name")
    slot: str = Field(..., description="Slot")
    course_code: str = Field(..., description="Course code")
    class_size: Optional[int] = Field(None, ge=10, le=200)

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
    raw_scores_json: Optional[str]
    updated_at: datetime
