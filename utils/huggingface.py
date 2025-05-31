import requests
import json
from typing import Dict, Any, List, Optional
from config.settings import settings
from datetime import datetime, timedelta

class HuggingFaceService:
    def __init__(self):
        self.api_token = settings.huggingface_api_token
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        
        # Model endpoints
        self.qa_model = "deepset/roberta-base-squad2"
        self.text_generation_model = "microsoft/DialoGPT-medium"
        self.summarization_model = "facebook/bart-large-cnn"
        # Add Mistral AI for diet generation
        self.mistral_model = "mistralai/Mistral-7B-Instruct-v0.3"
    
    async def query_model(self, model_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generic method to query Hugging Face models"""
        api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        
        try:
            response = requests.post(api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying Hugging Face API: {e}")
            return {"error": str(e)}
    
    async def generate_diet_plan(self, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PCOS-friendly diet plan using Mistral AI"""
        
        # Extract user preferences
        dietary_style = user_preferences.get('dietary_style', 'vegetarian')
        calorie_goal = user_preferences.get('calorie_goal', 1800)
        days = user_preferences.get('days', 7)
        allergies = user_preferences.get('allergies', [])
        symptoms = user_preferences.get('symptoms', [])
        cuisine_preference = user_preferences.get('cuisine', 'mixed')
        budget = user_preferences.get('budget', 'moderate')
        
        # Create detailed prompt for Mistral
        prompt = self._create_diet_prompt(
            dietary_style, calorie_goal, days, allergies, symptoms, cuisine_preference, budget
        )
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1500,
                "temperature": 0.7,
                "do_sample": True,
                "top_p": 0.9,
                "return_full_text": False
            }
        }
        
        try:
            result = await self.query_model(self.mistral_model, payload)
            
            if "error" in result:
                return {
                    "success": False,
                    "error": "Unable to generate diet plan at the moment. Please try again.",
                    "fallback_plan": self._get_fallback_diet_plan(dietary_style, days)
                }
            
            # Parse the generated response
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', '')
            else:
                generated_text = str(result)
            
            # Structure the response
            structured_plan = self._parse_diet_response(generated_text, days)
            
            return {
                "success": True,
                "diet_plan": structured_plan,
                "user_preferences": user_preferences,
                "generated_at": datetime.utcnow().isoformat(),
                "grocery_list": self._generate_grocery_list(structured_plan)
            }
            
        except Exception as e:
            print(f"Error generating diet plan: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_plan": self._get_fallback_diet_plan(dietary_style, days)
            }
    
    def _create_diet_prompt(self, dietary_style: str, calorie_goal: int, days: int, 
                           allergies: List[str], symptoms: List[str], cuisine: str, budget: str) -> str:
        """Create detailed prompt for Mistral AI"""
        
        allergy_text = f" avoiding {', '.join(allergies)}" if allergies else ""
        symptom_text = f" focusing on managing {', '.join(symptoms)}" if symptoms else ""
        
        prompt = f"""You are a certified nutritionist specializing in PCOS (Polycystic Ovary Syndrome) management. Create a detailed {days}-day {dietary_style} meal plan for a woman with PCOS.

REQUIREMENTS:
- Target: {calorie_goal} calories per day
- Diet style: {dietary_style}
- Cuisine preference: {cuisine}
- Budget: {budget}
- Allergies/Restrictions: {allergy_text}
- PCOS symptoms to address: {symptom_text}

PCOS NUTRITION GUIDELINES:
- Low glycemic index foods (GI < 55)
- Anti-inflammatory ingredients
- Balanced macros: 40% carbs, 30% protein, 30% healthy fats
- High fiber content (25-35g daily)
- Omega-3 rich foods
- Minimal processed foods
- Blood sugar stabilizing meals

FORMAT your response as:
DAY 1:
BREAKFAST: [Meal name] - [calories]cal
Ingredients: [list]
Prep time: [time]

LUNCH: [Meal name] - [calories]cal
Ingredients: [list]
Prep time: [time]

DINNER: [Meal name] - [calories]cal
Ingredients: [list]
Prep time: [time]

SNACK: [Meal name] - [calories]cal
Ingredients: [list]

[Continue for all {days} days]

DAILY TIPS:
- [PCOS-specific tip for the day]

Begin the meal plan:"""
        
        return prompt
    
    def _parse_diet_response(self, generated_text: str, days: int) -> Dict[str, Any]:
        """Parse Mistral's response into structured format"""
        try:
            lines = generated_text.split('\n')
            parsed_plan = {}
            current_day = None
            current_meal = None
            
            for line in lines:
                line = line.strip()
                
                # Check for day headers
                if line.startswith('DAY '):
                    current_day = line.replace(':', '').lower().replace(' ', '_')
                    parsed_plan[current_day] = {}
                
                # Check for meal types
                elif any(meal in line.upper() for meal in ['BREAKFAST:', 'LUNCH:', 'DINNER:', 'SNACK:']):
                    meal_parts = line.split(':')
                    if len(meal_parts) >= 2:
                        meal_type = meal_parts[0].lower()
                        meal_info = meal_parts[1].strip()
                        
                        if current_day:
                            parsed_plan[current_day][meal_type] = {
                                'name': meal_info.split(' - ')[0],
                                'calories': self._extract_calories(meal_info),
                                'ingredients': [],
                                'prep_time': ''
                            }
                            current_meal = meal_type
                
                # Check for ingredients
                elif line.startswith('Ingredients:') and current_day and current_meal:
                    ingredients = line.replace('Ingredients:', '').strip()
                    parsed_plan[current_day][current_meal]['ingredients'] = [
                        ing.strip() for ing in ingredients.split(',')
                    ]
                
                # Check for prep time
                elif line.startswith('Prep time:') and current_day and current_meal:
                    prep_time = line.replace('Prep time:', '').strip()
                    parsed_plan[current_day][current_meal]['prep_time'] = prep_time
            
            return parsed_plan
            
        except Exception as e:
            print(f"Error parsing diet response: {e}")
            return self._get_fallback_structured_plan(days)
    
    def _extract_calories(self, text: str) -> int:
        """Extract calorie information from text"""
        import re
        calorie_match = re.search(r'(\d+)\s*cal', text, re.IGNORECASE)
        return int(calorie_match.group(1)) if calorie_match else 0
    
    def _generate_grocery_list(self, diet_plan: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate categorized grocery list from diet plan"""
        grocery_categories = {
            'proteins': [],
            'vegetables': [],
            'fruits': [],
            'grains': [],
            'dairy': [],
            'pantry': [],
            'spices': []
        }
        
        # Common PCOS-friendly ingredients categorization
        protein_keywords = ['chicken', 'fish', 'salmon', 'tuna', 'eggs', 'tofu', 'lentils', 'beans', 'chickpeas', 'quinoa']
        vegetable_keywords = ['spinach', 'kale', 'broccoli', 'cauliflower', 'bell pepper', 'zucchini', 'cucumber', 'tomato']
        fruit_keywords = ['berries', 'apple', 'orange', 'avocado', 'lemon', 'lime']
        grain_keywords = ['oats', 'brown rice', 'quinoa', 'whole wheat']
        dairy_keywords = ['greek yogurt', 'cottage cheese', 'almond milk', 'coconut milk']
        pantry_keywords = ['olive oil', 'nuts', 'seeds', 'vinegar', 'honey']
        
        all_ingredients = set()
        
        # Extract all ingredients from the diet plan
        for day_meals in diet_plan.values():
            if isinstance(day_meals, dict):
                for meal_info in day_meals.values():
                    if isinstance(meal_info, dict) and 'ingredients' in meal_info:
                        all_ingredients.update(meal_info['ingredients'])
        
        # Categorize ingredients
        for ingredient in all_ingredients:
            ingredient_lower = ingredient.lower()
            categorized = False
            
            for keyword in protein_keywords:
                if keyword in ingredient_lower:
                    grocery_categories['proteins'].append(ingredient)
                    categorized = True
                    break
            
            if not categorized:
                for keyword in vegetable_keywords:
                    if keyword in ingredient_lower:
                        grocery_categories['vegetables'].append(ingredient)
                        categorized = True
                        break
            
            if not categorized:
                for keyword in fruit_keywords:
                    if keyword in ingredient_lower:
                        grocery_categories['fruits'].append(ingredient)
                        categorized = True
                        break
            
            if not categorized:
                for keyword in grain_keywords:
                    if keyword in ingredient_lower:
                        grocery_categories['grains'].append(ingredient)
                        categorized = True
                        break
            
            if not categorized:
                for keyword in dairy_keywords:
                    if keyword in ingredient_lower:
                        grocery_categories['dairy'].append(ingredient)
                        categorized = True
                        break
            
            if not categorized:
                for keyword in pantry_keywords:
                    if keyword in ingredient_lower:
                        grocery_categories['pantry'].append(ingredient)
                        categorized = True
                        break
            
            if not categorized:
                grocery_categories['pantry'].append(ingredient)
        
        # Remove duplicates and empty categories
        for category in grocery_categories:
            grocery_categories[category] = list(set(grocery_categories[category]))
            grocery_categories[category] = [item for item in grocery_categories[category] if item.strip()]
        
        return {k: v for k, v in grocery_categories.items() if v}
    
    def _get_fallback_diet_plan(self, dietary_style: str, days: int) -> Dict[str, Any]:
        """Provide a basic fallback diet plan"""
        return {
            "day_1": {
                "breakfast": {
                    "name": "PCOS-Friendly Oatmeal Bowl",
                    "calories": 350,
                    "ingredients": ["1/2 cup steel-cut oats", "1 tbsp almond butter", "1/4 cup berries", "1 tsp cinnamon"],
                    "prep_time": "10 minutes"
                },
                "lunch": {
                    "name": "Quinoa Power Salad",
                    "calories": 450,
                    "ingredients": ["1/2 cup quinoa", "2 cups spinach", "1/4 cup chickpeas", "1 tbsp olive oil", "lemon juice"],
                    "prep_time": "15 minutes"
                },
                "dinner": {
                    "name": "Grilled Salmon with Vegetables",
                    "calories": 500,
                    "ingredients": ["4 oz salmon", "1 cup broccoli", "1/2 cup sweet potato", "herbs", "olive oil"],
                    "prep_time": "25 minutes"
                },
                "snack": {
                    "name": "Greek Yogurt with Nuts",
                    "calories": 200,
                    "ingredients": ["1/2 cup Greek yogurt", "1 tbsp walnuts", "1 tsp honey"],
                    "prep_time": "2 minutes"
                }
            }
        }
    
    def _get_fallback_structured_plan(self, days: int) -> Dict[str, Any]:
        """Get structured fallback plan"""
        base_plan = self._get_fallback_diet_plan("mixed", 1)
        return {f"day_{i+1}": base_plan["day_1"] for i in range(days)}
    
    # Keep all your existing methods for chat functionality
    async def answer_question(self, question: str, context: str) -> str:
        """Answer questions using Q&A model"""
        payload = {
            "inputs": {
                "question": question,
                "context": context
            }
        }
        
        result = await self.query_model(self.qa_model, payload)
        
        if "error" in result:
            return "I'm sorry, I couldn't process your question at the moment. Please try again later."
        
        if "answer" in result:
            return result["answer"]
        
        return "I couldn't find a specific answer to your question in my knowledge base."
    
    async def generate_response(self, message: str, context: str = "") -> str:
        """Generate conversational response using the context and PCOS knowledge"""
        
        # Check if it's a PCOS-related question
        pcos_context = self.get_pcos_context()
        
        # If it's a direct question, use Q&A
        if any(word in message.lower() for word in ["what", "how", "why", "when", "where", "should", "can", "is", "are"]):
            return await self.answer_question(message, pcos_context)
        
        # For general conversation, provide PCOS-focused response
        return await self.generate_pcos_response(message)
    
    async def generate_pcos_response(self, message: str) -> str:
        """Generate PCOS-specific responses"""
        message_lower = message.lower()
        
        # Diet-related responses
        if any(word in message_lower for word in ["diet", "food", "eat", "meal", "nutrition", "plan"]):
            return self.get_diet_advice()
        
        # Symptom-related responses
        elif any(word in message_lower for word in ["symptom", "pain", "cramp", "bloating", "period"]):
            return self.get_symptom_advice()
        
        # Exercise-related responses
        elif any(word in message_lower for word in ["exercise", "workout", "gym", "fitness"]):
            return self.get_exercise_advice()
        
        # General greeting or support
        elif any(word in message_lower for word in ["hello", "hi", "help", "support"]):
            return "Hello! I'm your PCOS Health Assistant. I can help you with PCOS-friendly diet suggestions, symptom management, exercise recommendations, and answer questions about PCOS. What would you like to know about today?"
        
        # Default response
        else:
            return "I'm here to help with your PCOS journey. You can ask me about diet, symptoms, exercise, or any PCOS-related questions!"
    
    def get_pcos_context(self) -> str:
        """Basic PCOS knowledge context"""
        return """
        PCOS (Polycystic Ovary Syndrome) is a hormonal disorder affecting women of reproductive age. 
        
        Key aspects of PCOS management:
        
        Diet: Focus on low glycemic index foods, anti-inflammatory foods, lean proteins, and healthy fats. 
        Avoid processed foods, sugary drinks, and refined carbohydrates. Good foods include leafy greens, 
        berries, nuts, fish, lean meats, quinoa, and legumes.
        
        Exercise: Regular physical activity helps improve insulin sensitivity. Combination of cardio and 
        strength training is recommended. Aim for at least 150 minutes of moderate exercise per week.
        
        Common symptoms: Irregular periods, weight gain, acne, hair growth, hair loss, mood changes, 
        insulin resistance, and difficulty losing weight.
        
        Lifestyle: Stress management, adequate sleep (7-9 hours), and maintaining a healthy weight 
        are crucial for managing PCOS symptoms.
        
        Supplements: Some women benefit from inositol, vitamin D, omega-3 fatty acids, and chromium, 
        but consult healthcare providers before starting any supplements.
        """
    
    def get_diet_advice(self) -> str:
        """Return diet advice for PCOS"""
        return """For PCOS-friendly nutrition, focus on:

✅ **Include:**
- Low glycemic index foods (quinoa, sweet potatoes, oats)
- Anti-inflammatory foods (fatty fish, leafy greens, berries)
- Lean proteins (chicken, fish, legumes, tofu)
- Healthy fats (avocado, nuts, olive oil)
- Fiber-rich foods (vegetables, fruits, whole grains)

❌ **Limit:**
- Processed and refined foods
- Sugary drinks and snacks
- White bread and pasta
- Fried foods
- Excessive dairy (some women are sensitive)

💡 **Tip:** Eat balanced meals with protein, healthy fats, and complex carbs to help stabilize blood sugar levels.

Would you like me to create a personalized meal plan for you? Just ask for a "diet plan" and I can generate one based on your preferences!"""
    
    def get_symptom_advice(self) -> str:
        """Return symptom management advice"""
        return """Common PCOS symptoms and management tips:

🩸 **Irregular Periods:** Maintain healthy weight, manage stress, consider spearmint tea
🤰 **Weight Management:** Focus on whole foods, portion control, regular exercise
😔 **Mood Changes:** Regular exercise, adequate sleep, stress reduction techniques
💊 **Insulin Resistance:** Low GI diet, regular meals, strength training
🌿 **Natural Support:** Cinnamon, spearmint tea, and inositol may help

⚠️ **Important:** Always consult your healthcare provider for personalized treatment plans and before making significant changes to your routine."""
    
    def get_exercise_advice(self) -> str:
        """Return exercise advice for PCOS"""
        return """PCOS-friendly exercise recommendations:

🏃‍♀️ **Cardio (3-4x/week):**
- Brisk walking, swimming, cycling
- 30-45 minutes moderate intensity
- Helps with insulin sensitivity

💪 **Strength Training (2-3x/week):**
- Focus on major muscle groups
- Improves insulin sensitivity and metabolism
- Can help with weight management

🧘‍♀️ **Stress-Reducing Activities:**
- Yoga, pilates, tai chi
- Helps manage cortisol levels
- Supports hormonal balance

💡 **Start gradually and listen to your body. Consistency is more important than intensity!**"""

# Initialize the service
hf_service = HuggingFaceService()