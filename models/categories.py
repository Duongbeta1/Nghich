from models.mongo import mongo_database

collection = mongo_database['categories']


async def get_all_categories():
  categories = await collection.find().to_list(length=None)
  return [category['name'] for category in categories]
