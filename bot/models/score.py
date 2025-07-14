from sqlalchemy import Column, String, ARRAY, DateTime, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
import uuid

Base = declarative_base()

class StageEnum(enum.Enum):
    one = "1"
    two = "2"
    three = "3"
    four = "4"
    five = "5"
    six = "6"
    seven = "7"
    eight = "8"
    bonus = "bonus"

class TrackEnum(enum.Enum):
    backend = "backend"
    frontend = "frontend"
    design = "design"
    devops = "devops"
    data_analysis = "data_analysis"
    project_management = "project_management"

class Score(Base):
    __tablename__ = "scores"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    slack_username = Column(String, nullable=False)
    slack_user_id = Column(String, nullable=False)
    points = Column(Float, nullable=False, default=0.0)
    stage = Column(Enum(StageEnum), nullable=False)
    track = Column(Enum(TrackEnum), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    uploader_id = Column(String, nullable=False)
    uploader_username = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
