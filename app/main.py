from fastapi import FastAPI

from app.config import settings
from app.database import engine, Base
from app.routers import applications

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0")

app.include_router(applications.router)


@app.get("/")
def root():
    return {"message": "Job Tracker API is running"}