from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.database import create_tables
from app.core.config import settings
from app.routers import (
    auth_router,
    profile_router,
    projects_router,
    applications_router,
    collaborations_router,
    conversations_router,
    notifications_router,
    reports_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.PRODUCTION else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Collabers API (Production: {settings.PRODUCTION})")
    await create_tables()
    yield
    logger.info("Shutting down Collabers API")


app = FastAPI(
    title="Collabers API",
    description="Find your project partner. Build something together.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.PRODUCTION else "/docs",
    redoc_url=None if settings.PRODUCTION else "/redoc",
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
allowed_origins = [settings.FRONTEND_URL]
if not settings.PRODUCTION:
    allowed_origins.extend(["http://localhost:1712", "http://127.0.0.1:1712"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(applications_router, prefix="/api")
app.include_router(collaborations_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to Collabers API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full error for debugging (server-side only)
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    
    # Return generic error to client (don't expose internal details)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )
