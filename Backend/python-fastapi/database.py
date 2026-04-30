import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("DB_NAME", "medical-requests")

# Single client instance reused across the app
client = AsyncIOMotorClient(MONGO_URI)
db     = client[DB_NAME]

def get_collection(name: str):
    """Return a MongoDB collection by name."""
    return db[name]

async def ping_db():
    """Check if MongoDB is reachable — used in health check."""
    try:
        await client.admin.command("ping")
        return True
    except Exception:
        return False