from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.MONGODB_URL)
database = client[settings.DATABASE_NAME]

user_collection = database.get_collection("users")
donation_request_collection = database.get_collection("donation_requests")
donation_history_collection = database.get_collection("donation_history")