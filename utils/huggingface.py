import requests
import json
from typing import Dict, Any, List
from config.settings import settings

class HuggingFaceService:
    def __init__(self):
        self.api_token = settings.huggingface_api_token
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        
        # Model endpoints
        self.qa_model = "deepset/roberta-base-squad2"
        self.text_generation_model = "microsoft/DialoGPT-medium"
        self.summarization_model = "facebook/bart-large-cnn"
    
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
        if any(word in message_lower for word in ["diet", "food", "eat", "meal", "nutrition"]):
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

💡 **Tip:** Eat balanced meals with protein, healthy fats, and complex carbs to help stabilize blood sugar levels."""
    
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