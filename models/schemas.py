from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
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

# Diet Generation Models
class DietaryStyle(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    OMNIVORE = "omnivore"
    KETO = "keto"
    MEDITERRANEAN = "mediterranean"

class CuisinePreference(str, Enum):
    MIXED = "mixed"
    INDIAN = "indian"
    MEDITERRANEAN = "mediterranean"
    ASIAN = "asian"
    AMERICAN = "american"
    MEXICAN = "mexican"

class Budget(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

class PCOSSymptom(str, Enum):
    INSULIN_RESISTANCE = "insulin_resistance"
    WEIGHT_GAIN = "weight_gain"
    IRREGULAR_PERIODS = "irregular_periods"
    BLOATING = "bloating"
    MOOD_SWINGS = "mood_swings"
    ACNE = "acne"
    HAIR_LOSS = "hair_loss"
    FATIGUE = "fatigue"

class DietPreferences(BaseModel):
    dietary_style: DietaryStyle = DietaryStyle.VEGETARIAN
    calorie_goal: int = Field(default=1800, ge=1200, le=3000)
    days: int = Field(default=7, ge=1, le=14)
    allergies: List[str] = Field(default_factory=list)
    symptoms: List[PCOSSymptom] = Field(default_factory=list)
    cuisine: CuisinePreference = CuisinePreference.MIXED
    budget: Budget = Budget.MODERATE
    avoid_foods: List[str] = Field(default_factory=list)
    preferred_foods: List[str] = Field(default_factory=list)

class MealInfo(BaseModel):
    name: str
    calories: int
    ingredients: List[str]
    prep_time: str
    instructions: Optional[str] = None

class DayMeals(BaseModel):
    breakfast: Optional[MealInfo] = None
    lunch: Optional[MealInfo] = None
    dinner: Optional[MealInfo] = None
    snack: Optional[MealInfo] = None

class GroceryList(BaseModel):
    proteins: List[str] = Field(default_factory=list)
    vegetables: List[str] = Field(default_factory=list)
    fruits: List[str] = Field(default_factory=list)
    grains: List[str] = Field(default_factory=list)
    dairy: List[str] = Field(default_factory=list)
    pantry: List[str] = Field(default_factory=list)
    spices: List[str] = Field(default_factory=list)

class DietPlanResponse(BaseModel):
    success: bool
    diet_plan: Optional[Dict[str, DayMeals]] = None
    user_preferences: Optional[DietPreferences] = None
    generated_at: Optional[str] = None
    grocery_list: Optional[GroceryList] = None
    error: Optional[str] = None
    fallback_plan: Optional[Dict[str, Any]] = None

class SavedDietPlan(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    plan_name: str
    diet_plan: Dict[str, Any]
    preferences: DietPreferences
    grocery_list: GroceryList
    created_at: datetime
    is_active: bool = True
    
    class Config:
        populate_by_name = True

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

# Quick Diet Request (simplified)
class QuickDietRequest(BaseModel):
    dietary_style: str = "vegetarian"
    days: int = Field(default=3, ge=1, le=7)
    calorie_goal: int = Field(default=1800, ge=1200, le=3000)
    symptoms: List[str] = Field(default_factory=list)

# General Response Models
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str