from fastapi import APIRouter
from .jobs import router as jobs_router
from .printers import router as printers_router
from .templates import router as templates_router
from .template_editor import router as template_editor_router
from .users import router as users_router
from .auth import router as auth_router
from .operator import router as operator_router
from .agent import router as agent_router

# Main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(printers_router, prefix="/printers", tags=["Printers"])
api_router.include_router(templates_router, prefix="/templates", tags=["Templates"])
api_router.include_router(template_editor_router, prefix="/templates", tags=["Template Editor"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(operator_router, prefix="/operator", tags=["Operator Console"])
api_router.include_router(agent_router, prefix="/agent", tags=["Print Agent"])

