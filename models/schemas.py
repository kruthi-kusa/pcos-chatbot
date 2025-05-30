from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# User Models
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: str
    created_at: datetime
    
    class Config:
        populate_by_name = True

class UserInDB(User):
    hashed_password: str

# Auth Models
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None

# Chat Models
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)

class ChatResponse(BaseModel):
    message_id: str
    response: str
    timestamp: datetime

# Symptom Models
class SymptomSeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

class SymptomEntry(BaseModel):
    symptom_type: str  # e.g., "bloating", "cramps", "mood_swings"
    severity: SymptomSeverity
    date: datetime
    notes: Optional[str] = None

class SymptomLog(BaseModel):
    user_id: str
    symptoms: List[SymptomEntry]
    date: datetime

# Meal Plan Models
class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"

class Meal(BaseModel):
    name: str
    ingredients: List[str]
    calories: Optional[int] = None
    prep_time: Optional[str] = None
    instructions: Optional[str] = None

class MealPlan(BaseModel):
    user_id: str
    date: datetime
    meals: dict[MealType, Meal]
    total_calories: Optional[int] = None

# General Response Models
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str