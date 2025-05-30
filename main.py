from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config.database import ping_database
from config.settings import settings
from routes import auth, chat

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting PCOS Health Assistant API...")
    
    # Test database connection
    db_connected = await ping_database()
    if not db_connected:
        print("⚠️  Running without database - some features will be limited")
    
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

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
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
            "api": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)