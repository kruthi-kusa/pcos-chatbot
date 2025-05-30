import asyncio
import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

async def test_mongodb():
    """Test MongoDB connection independently"""
    mongodb_url = os.getenv("MONGODB_URL")
    
    if not mongodb_url:
        print("❌ MONGODB_URL not found in .env file")
        return
    
    print(f"🔗 Testing connection to: {mongodb_url[:50]}...")
    
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        # Test database access
        db = client["pcos_assistant"]
        collection = db["test"]
        
        # Insert test document
        result = await collection.insert_one({"test": "connection"})
        print(f"✅ Test document inserted: {result.inserted_id}")
        
        # Clean up test document
        await collection.delete_one({"_id": result.inserted_id})
        print("✅ Test document deleted")
        
        client.close()
        print("🎉 MongoDB Atlas connection working perfectly!")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check username/password in connection string")
        print("2. Verify IP whitelist in Network Access")
        print("3. Ensure user has proper permissions")
        print("4. Check if cluster is running")

if __name__ == "__main__":
    asyncio.run(test_mongodb())