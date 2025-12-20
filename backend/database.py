from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = AsyncIOMotorClient(settings.mongodb_url)
database = client[settings.database_name]
users_collection = database.get_collection("users")
