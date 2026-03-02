from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.application import Application
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationResponse, status_code=201)
def create_application(data: ApplicationCreate, db: Session = Depends(get_db)):
    application = Application(
        company=data.company,
        job_title=data.job_title,
        url=data.url,
        status=data.status,
        applied_date=data.applied_date or datetime.now(timezone.utc),
        notes=data.notes,
        tags=data.tags,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/", response_model=list[ApplicationResponse])
def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
):
    query = db.query(Application)

    if status:
        query = query.filter(Application.status == status)
    if tag:
        query = query.filter(Application.tags.any(tag))

    query = query.order_by(Application.applied_date.desc())
    return query.offset(skip).limit(limit).all()


@router.get("/stats/summary")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Application.id)).scalar()

    if total == 0:
        return {"total_applications": 0, "by_status": {}, "most_recent": None}

    status_counts = (
        db.query(Application.status, func.count(Application.id))
        .group_by(Application.status)
        .all()
    )

    most_recent = (
        db.query(Application)
        .order_by(Application.applied_date.desc())
        .first()
    )

    return {
        "total_applications": total,
        "by_status": {status: count for status, count in status_counts},
        "most_recent": {
            "company": most_recent.company,
            "job_title": most_recent.job_title,
            "applied_date": most_recent.applied_date,
        },
    }


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int, data: ApplicationUpdate, db: Session = Depends(get_db)
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(application, key, value)

    application.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(application)
    return application


@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(application)
    db.commit()