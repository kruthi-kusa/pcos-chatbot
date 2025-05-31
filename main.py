from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config.database import ping_database
from config.settings import settings
from routes import auth, chat
import os

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting PCOS Health Assistant API...")
    
    # Test database connection
    db_connected = await ping_database()
    if not db_connected:
        print("⚠️  Running without database - some features will be limited")
    else:
        print("✅ Database connected successfully")
    
    print(f"🌐 CORS enabled for: {settings.frontend_url}")
    print("🤖 Hugging Face integration ready")
    print("📱 API is ready to serve requests!")
    
    yield
    
    # Shutdown
    print("👋 Shutting down PCOS Health Assistant API...")

# Create FastAPI app
app = FastAPI(
    title="PCOS Health Assistant API",
    description="AI-powered assistant for PCOS management and support",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Updated for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "https://*.vercel.app",  # Allow Vercel preview URLs
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to PCOS Health Assistant API",
        "version": "1.0.0",
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "features": [
            "User Authentication",
            "AI-Powered Chat Assistant",
            "PCOS Knowledge Base",
            "Symptom Tracking (Coming Soon)",
            "Meal Planning (Coming Soon)"
        ]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        db_status = await ping_database()
        return {
            "status": "healthy",
            "database": "connected" if db_status else "disconnected",
            "api": "running",
            "environment": os.getenv("ENVIRONMENT", "production")
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)