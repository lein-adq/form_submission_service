"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.settings import settings
from app.core.exceptions import (
    DomainException,
    domain_exception_handler,
    generic_exception_handler,
)
from app.core.logging import logger
from app.core.middleware.auth_logging import auth_logging_middleware
from app.core.middleware.rate_limit import limiter

# RLS middleware removed - RLS context is now applied at dependency level
# from app.core.middleware.rls_middleware import rls_middleware
from app.modules.auth.api.router import router as auth_router
from app.modules.forms.api.router import router as forms_router
from app.modules.submissions.api.router import router as submissions_router
from app.modules.workspaces.api.router import router as workspaces_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting FormCore application...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"JWT Token Expiry: {settings.jwt_access_token_expire_minutes} minutes")
    yield
    logger.info("Shutting down FormCore application...")


app = FastAPI(
    title="FormCore",
    description="Form Backend-as-a-Service (FBaaS)",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add custom middleware (order matters - last added runs first)
# 1. Auth logging (logs all requests with user context)
app.middleware("http")(auth_logging_middleware)
# 2. RLS context is now handled at the dependency level (get_db_with_rls_context)
#    Middleware-based RLS has been removed to avoid session mismatch issues

# Register exception handlers
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")
app.include_router(forms_router, prefix="/api/v1")
app.include_router(submissions_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    """Health check endpoint with system information."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "auth": {
            "jwt_algorithm": settings.jwt_algorithm,
            "access_token_expiry_minutes": settings.jwt_access_token_expire_minutes,
            "refresh_token_expiry_days": settings.jwt_refresh_token_expire_days,
        },
        "features": {
            "rls_enabled": True,
            "multi_tenant": True,
            "rate_limiting": True,
            "auth_logging": True,
        },
    }


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "FormCore",
        "version": "0.1.0",
        "description": "Form Backend-as-a-Service (FBaaS)",
        "docs": "/docs",
        "health": "/health",
    }
