from fastapi import APIRouter

from app.routes.auth import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.health import router as health_router
from app.routes.interview import router as interview_router
from app.routes.public_speaking import router as public_speaking_router
from app.routes.recordings import router as recordings_router
from app.routes.reports import router as reports_router
from app.routes.resume_analysis import router as resume_analysis_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(interview_router)
api_router.include_router(public_speaking_router)
api_router.include_router(recordings_router)
api_router.include_router(reports_router)
api_router.include_router(resume_analysis_router)
