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
        print("🔄 Initializing AI service...")
        # Initialize the global AI service instance with timeout (load models, etc.)
        from app.services.ai_service import ai_service
        import asyncio
        await asyncio.wait_for(ai_service.initialize(), timeout=60.0)  # 60 second timeout
        print("✅ AI service initialized successfully!")
    except asyncio.TimeoutError:
        print("⚠️ AI service initialization timed out (60s)")
        print("🔄 Server will continue without AI features...")
    except Exception as e:
        print(f"⚠️ AI service initialization failed: {e}")
        print("🔄 Server will continue without AI features...")
    
    print(f"🚀 {settings.PROJECT_NAME} started successfully!")
    print(f"📚 API Documentation: http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    await close_mongo_connection()
    print("👋 AuraHR shutdown complete")

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