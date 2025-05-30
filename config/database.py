import motor.motor_asyncio
from config.settings import settings

client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
database = client[settings.database_name]

# Collections
users_collection = database.get_collection("users")
chat_history_collection = database.get_collection("chat_history")
symptoms_collection = database.get_collection("symptoms")
meal_plans_collection = database.get_collection("meal_plans")

async def ping_database():
    """Test database connection"""
    try:
        await client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        return True
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return False