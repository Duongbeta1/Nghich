import motor.motor_asyncio
import os

CONNECTION_STRING = os.environ.get("MONGO_CONNECTION_STRING")
client = motor.motor_asyncio.AsyncIOMotorClient(CONNECTION_STRING)
mongo_database = client['learnhub']
