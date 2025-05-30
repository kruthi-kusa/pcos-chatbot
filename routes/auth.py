from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from config.database import users_collection
from config.settings import settings
from models.schemas import UserCreate, UserLogin, Token, User, MessageResponse
from utils.auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_user_by_email
)
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user document
    user_doc = {
        "name": user_data.name,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    # Insert user into database
    result = await users_collection.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user_data.email}, 
        expires_delta=access_token_expires
    )
    
    # Prepare user response
    user_response = User(
        id=str(user_doc["_id"]),
        name=user_doc["name"],
        email=user_doc["email"],
        created_at=user_doc["created_at"]
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login user and return access token"""
    
    # Authenticate user
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["email"]}, 
        expires_delta=access_token_expires
    )
    
    # Prepare user response
    user_response = User(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"]
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/logout", response_model=MessageResponse)
async def logout():
    """Logout user (client should remove token)"""
    return MessageResponse(message="Successfully logged out")