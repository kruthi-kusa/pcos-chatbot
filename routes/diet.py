from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from models.schemas import (
    DietPreferences, 
    DietPlanResponse, 
    QuickDietRequest,
    SavedDietPlan,
    User,
    MessageResponse
)
from utils.huggingface import hf_service
from utils.auth import get_current_user, generate_unique_id
from config.database import database
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/diet", tags=["diet"])

# Collection for saved diet plans
diet_plans_collection = database.get_collection("diet_plans")

@router.post("/generate", response_model=DietPlanResponse)
async def generate_diet_plan(preferences: DietPreferences):
    """Generate a personalized PCOS-friendly diet plan using Mistral AI"""
    
    try:
        # Convert preferences to dict for the service
        user_preferences = {
            "dietary_style": preferences.dietary_style.value,
            "calorie_goal": preferences.calorie_goal,
            "days": preferences.days,
            "allergies": preferences.allergies,
            "symptoms": [symptom.value for symptom in preferences.symptoms],
            "cuisine": preferences.cuisine.value,
            "budget": preferences.budget.value,
            "avoid_foods": preferences.avoid_foods,
            "preferred_foods": preferences.preferred_foods
        }
        
        # Generate diet plan using Mistral AI
        result = await hf_service.generate_diet_plan(user_preferences)
        
        if not result["success"]:
            return DietPlanResponse(
                success=False,
                error=result.get("error", "Failed to generate diet plan"),
                fallback_plan=result.get("fallback_plan")
            )
        
        return DietPlanResponse(
            success=True,
            diet_plan=result["diet_plan"],
            user_preferences=preferences,
            generated_at=result["generated_at"],
            grocery_list=result["grocery_list"]
        )
        
    except Exception as e:
        print(f"Diet generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating diet plan: {str(e)}"
        )

@router.post("/quick-generate", response_model=DietPlanResponse)
async def quick_generate_diet_plan(request: QuickDietRequest):
    """Generate a quick diet plan with minimal inputs"""
    
    try:
        # Convert to full preferences
        user_preferences = {
            "dietary_style": request.dietary_style,
            "calorie_goal": request.calorie_goal,
            "days": request.days,
            "allergies": [],
            "symptoms": request.symptoms,
            "cuisine": "mixed",
            "budget": "moderate",
            "avoid_foods": [],
            "preferred_foods": []
        }
        
        result = await hf_service.generate_diet_plan(user_preferences)
        
        if not result["success"]:
            return DietPlanResponse(
                success=False,
                error=result.get("error", "Failed to generate diet plan"),
                fallback_plan=result.get("fallback_plan")
            )
        
        return DietPlanResponse(
            success=True,
            diet_plan=result["diet_plan"],
            generated_at=result["generated_at"],
            grocery_list=result["grocery_list"]
        )
        
    except Exception as e:
        print(f"Quick diet generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating quick diet plan: {str(e)}"
        )

@router.post("/save", response_model=MessageResponse)
async def save_diet_plan(
    plan_name: str,
    diet_plan_data: dict,
    preferences: DietPreferences,
    grocery_list: dict,
    current_user: User = Depends(get_current_user)
):
    """Save a generated diet plan for the authenticated user"""
    
    try:
        # Create diet plan document
        diet_plan_doc = {
            "user_id": current_user.id,
            "plan_name": plan_name,
            "diet_plan": diet_plan_data,
            "preferences": preferences.dict(),
            "grocery_list": grocery_list,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Insert into database
        result = await diet_plans_collection.insert_one(diet_plan_doc)
        
        if result.inserted_id:
            return MessageResponse(message=f"Diet plan '{plan_name}' saved successfully!")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save diet plan"
            )
            
    except Exception as e:
        print(f"Save diet plan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving diet plan: {str(e)}"
        )

@router.get("/my-plans", response_model=List[SavedDietPlan])
async def get_my_diet_plans(current_user: User = Depends(get_current_user)):
    """Get all saved diet plans for the authenticated user"""
    
    try:
        plans_cursor = diet_plans_collection.find(
            {"user_id": current_user.id, "is_active": True}
        ).sort("created_at", -1)
        
        plans = await plans_cursor.to_list(length=100)
        
        # Convert to response models
        saved_plans = []
        for plan in plans:
            plan["id"] = str(plan["_id"])
            saved_plans.append(SavedDietPlan(**plan))
        
        return saved_plans
        
    except Exception as e:
        print(f"Get diet plans error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving diet plans: {str(e)}"
        )

@router.get("/plan/{plan_id}", response_model=SavedDietPlan)
async def get_diet_plan(plan_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific diet plan by ID"""
    
    try:
        plan = await diet_plans_collection.find_one({
            "_id": ObjectId(plan_id),
            "user_id": current_user.id,
            "is_active": True
        })
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet plan not found"
            )
        
        plan["id"] = str(plan["_id"])
        return SavedDietPlan(**plan)
        
    except Exception as e:
        print(f"Get diet plan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving diet plan: {str(e)}"
        )

@router.delete("/plan/{plan_id}", response_model=MessageResponse)
async def delete_diet_plan(plan_id: str, current_user: User = Depends(get_current_user)):
    """Delete a diet plan (soft delete)"""
    
    try:
        result = await diet_plans_collection.update_one(
            {"_id": ObjectId(plan_id), "user_id": current_user.id},
            {"$set": {"is_active": False}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet plan not found"
            )
        
        return MessageResponse(message="Diet plan deleted successfully")
        
    except Exception as e:
        print(f"Delete diet plan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting diet plan: {str(e)}"
        )

@router.get("/suggestions/symptoms")
async def get_symptom_based_suggestions():
    """Get diet suggestions based on common PCOS symptoms"""
    
    suggestions = {
        "insulin_resistance": {
            "focus": "Low glycemic index foods",
            "include": ["quinoa", "sweet potatoes", "legumes", "nuts", "leafy greens"],
            "avoid": ["white bread", "sugary drinks", "processed snacks", "white rice"],
            "tip": "Eat protein and fiber with each meal to stabilize blood sugar"
        },
        "weight_gain": {
            "focus": "Portion control and nutrient density",
            "include": ["lean proteins", "vegetables", "healthy fats", "whole grains"],
            "avoid": ["fried foods", "large portions", "liquid calories", "processed foods"],
            "tip": "Focus on feeling satisfied rather than full, eat slowly"
        },
        "irregular_periods": {
            "focus": "Hormone-balancing foods",
            "include": ["omega-3 rich fish", "flax seeds", "spearmint tea", "cinnamon"],
            "avoid": ["excess dairy", "inflammatory foods", "alcohol", "caffeine"],
            "tip": "Maintain consistent meal timing to support hormonal rhythm"
        },
        "bloating": {
            "focus": "Anti-inflammatory and easy-to-digest foods",
            "include": ["ginger", "fennel", "cucumber", "yogurt with probiotics"],
            "avoid": ["carbonated drinks", "beans initially", "cruciferous veggies", "artificial sweeteners"],
            "tip": "Eat smaller, more frequent meals and chew thoroughly"
        },
        "mood_swings": {
            "focus": "Blood sugar stability and mood-supporting nutrients",
            "include": ["complex carbs", "magnesium-rich foods", "omega-3s", "B vitamins"],
            "avoid": ["sugar spikes", "caffeine excess", "alcohol", "skipping meals"],
            "tip": "Regular meal timing and protein at each meal supports stable mood"
        }
    }
    
    return suggestions

@router.get("/meal-ideas/{meal_type}")
async def get_meal_ideas(meal_type: str, dietary_style: str = "vegetarian"):
    """Get PCOS-friendly meal ideas for specific meal types"""
    
    meal_ideas = {
        "breakfast": {
            "vegetarian": [
                {
                    "name": "PCOS Power Bowl",
                    "ingredients": ["Greek yogurt", "berries", "chia seeds", "almond butter", "cinnamon"],
                    "calories": 320,
                    "prep_time": "5 minutes"
                },
                {
                    "name": "Veggie Scramble",
                    "ingredients": ["eggs", "spinach", "bell peppers", "avocado", "herbs"],
                    "calories": 280,
                    "prep_time": "10 minutes"
                }
            ],
            "vegan": [
                {
                    "name": "Overnight Oats",
                    "ingredients": ["oats", "almond milk", "chia seeds", "berries", "nuts"],
                    "calories": 300,
                    "prep_time": "5 minutes prep, overnight"
                }
            ]
        },
        "lunch": {
            "vegetarian": [
                {
                    "name": "Quinoa Buddha Bowl",
                    "ingredients": ["quinoa", "roasted vegetables", "chickpeas", "tahini dressing"],
                    "calories": 450,
                    "prep_time": "25 minutes"
                }
            ]
        },
        "dinner": {
            "vegetarian": [
                {
                    "name": "Lentil Curry",
                    "ingredients": ["lentils", "coconut milk", "spinach", "spices", "brown rice"],
                    "calories": 400,
                    "prep_time": "30 minutes"
                }
            ]
        },
        "snack": {
            "vegetarian": [
                {
                    "name": "Apple with Almond Butter",
                    "ingredients": ["apple", "almond butter", "cinnamon"],
                    "calories": 180,
                    "prep_time": "2 minutes"
                }
            ]
        }
    }
    
    if meal_type in meal_ideas and dietary_style in meal_ideas[meal_type]:
        return meal_ideas[meal_type][dietary_style]
    else:
        return meal_ideas.get("breakfast", {}).get("vegetarian", [])