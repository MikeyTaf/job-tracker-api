from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    company: str = Field(..., min_length=1, max_length=200, examples=["Google"])
    job_title: str = Field(..., min_length=1, max_length=200, examples=["Backend Engineer"])
    url: Optional[str] = Field(None, max_length=500, examples=["https://careers.google.com/jobs/123"])
    status: str = Field("applied", examples=["applied"])
    applied_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, examples=["Referred by a friend"])
    tags: Optional[list[str]] = Field(None, examples=[["backend", "remote"]])


class ApplicationUpdate(BaseModel):
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    job_title: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = None
    applied_date: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None


class ApplicationResponse(BaseModel):
    id: int
    company: str
    job_title: str
    url: Optional[str]
    status: str
    applied_date: datetime
    notes: Optional[str]
    tags: Optional[list[str]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
