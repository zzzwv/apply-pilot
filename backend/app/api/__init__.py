from fastapi import APIRouter

from app.api.applications import router as applications_router
from app.api.auth import router as auth_router
from app.api.companies import router as companies_router
from app.api.company_intelligence import router as company_intelligence_router
from app.api.dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(companies_router)
api_router.include_router(company_intelligence_router)
api_router.include_router(applications_router)
api_router.include_router(dashboard_router)
