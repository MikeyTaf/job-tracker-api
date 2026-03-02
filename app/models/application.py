from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.postgresql import ARRAY

from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(200), nullable=False)
    job_title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="applied")
    applied_date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )