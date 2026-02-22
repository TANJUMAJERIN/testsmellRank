from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.mongodb_url)
database = client[settings.database_name]
users_collection = database.get_collection("users")
projects_collection = database.get_collection("projects")
runs_collection = database.get_collection("runs")
survey_responses_collection = database.get_collection("survey_responses")
