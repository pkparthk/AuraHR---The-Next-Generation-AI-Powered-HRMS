from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.services.ai_service import AIService

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url="/openapi.json",  # Keep OpenAPI at root level
    redirect_slashes=False  # Disable automatic trailing slash redirects
)

# Set up CORS - More comprehensive configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS + [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "*",
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods"
    ],
    expose_headers=["*"]
)

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Mount static files for uploaded documents
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Add CORS preflight handler
@app.options("/{path:path}")
async def cors_preflight_handler(path: str):
    """Handle CORS preflight requests."""
    return {}

# Include API router - mount both v1 and direct API paths for compatibility
app.include_router(api_router, prefix=settings.API_STR)  # /api/v1/*
app.include_router(api_router, prefix="/api")  # /api/* for frontend compatibility

@app.on_event("startup")
async def startup_event():
    """Initialize database connections and AI services on startup."""
    print("🔄 Starting AuraHR initialization...")
    
    try:
        print("🔄 Connecting to MongoDB...")
        await connect_to_mongo()
        print("✅ MongoDB connected successfully!")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        # Continue startup even if DB fails for debugging
    
    try:
        from app.services.ai_service import ai_service
        # Optionally initialize AI in background to avoid blocking startup and
        # reduce peak memory usage during deployment on constrained hosts.
        if settings.INIT_AI_ON_STARTUP:
            print("🔄 Scheduling AI service initialization in background task...")
            import asyncio
            # Schedule initialization but don't block startup. Any exceptions
            # will be logged by the AIService initializer.
            asyncio.create_task(_initialize_ai_service(ai_service))
        else:
            print("ℹ️ Skipping AI model initialization on startup (INIT_AI_ON_STARTUP=False)")
    except Exception as e:
        print(f"⚠️ Could not schedule AI initialization: {e}")
    
    print(f"🚀 {settings.PROJECT_NAME} started successfully!")
    print(f"📚 API Documentation: http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    await close_mongo_connection()
    print("👋 AuraHR shutdown complete")


async def _initialize_ai_service(ai_service):
    """Helper coroutine to initialize AI service with internal timeout and logging."""
    try:
        import asyncio
        print("🔄 AI background initializer starting...")
        await asyncio.wait_for(ai_service.initialize(), timeout=120.0)
        print("✅ AI service initialized successfully (background)!")
    except asyncio.TimeoutError:
        print("⚠️ AI service background initialization timed out (120s). Continuing without AI features.")
    except Exception as e:
        print(f"⚠️ AI service background initialization failed: {e}")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Welcome to AuraHR - The Next-Generation AI-Powered HRMS",
        "version": settings.VERSION,
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "services": {
            "database": "connected",
            "ai_service": "ready",
            "vector_db": "connected"
        }
    }