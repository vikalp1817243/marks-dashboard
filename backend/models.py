import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.mysql import CHAR
from database import Base

class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    max_marks = Column(Integer, nullable=False)
    class_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(CHAR(36), nullable=False, index=True)
    hashed_student_id = Column(String(64), nullable=False, index=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

class ExamScore(Base):
    __tablename__ = "exam_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(CHAR(36), nullable=False, index=True)
    score_value = Column(Float(precision=3), nullable=False)

class CachedStats(Base):
    __tablename__ = "cached_stats"

    session_id = Column(CHAR(36), primary_key=True)
    mean = Column(Float(precision=3), nullable=True)
    median = Column(Float(precision=3), nullable=True)
    mode = Column(Float(precision=3), nullable=True)
    std_dev = Column(Float(precision=3), nullable=True)
    min = Column(Float(precision=3), nullable=True)
    max = Column(Float(precision=3), nullable=True)
    q1 = Column(Float(precision=3), nullable=True)
    q3 = Column(Float(precision=3), nullable=True)
    count = Column(Integer, default=0)
    interpretation = Column(Text, nullable=True)
    histogram_json = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(CHAR(36), nullable=False, index=True)
    endpoint = Column(Text, nullable=False)
    p256dh_key = Column(Text, nullable=False)
    auth_key = Column(Text, nullable=False)
    notified = Column(Boolean, default=False)
