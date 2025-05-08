from models.mongo import mongo_database
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional, List

collection = mongo_database['quizzes']


async def add_quiz(quiz, user_id: str, is_public: bool = True):
  quiz_with_info = dict(quiz)

  for question in quiz_with_info.get('questions', []):
    if 'question_id' not in question:
      question['question_id'] = str(ObjectId())

  quiz_with_info.update({
      'user_id': user_id,
      'is_public': is_public,
      'created_date': datetime.now(timezone.utc),
      'last_modified_date': datetime.now(timezone.utc),
      'num_question': len(quiz_with_info.get('questions', []))
  })
  return await collection.insert_one(quiz_with_info)


async def update_quiz(quiz_id: str, update_data: dict):
  update_data['last_modified_date'] = datetime.now(timezone.utc)

  if 'questions' in update_data:
    update_data['num_question'] = len(update_data['questions'])

  object_id = ObjectId(quiz_id)

  result = await collection.update_one(
      {'_id': object_id},
      {'$set': update_data}
  )
  return result


async def delete_quiz(quiz_id: str):
  object_id = ObjectId(quiz_id)

  result = await collection.delete_one({'_id': object_id})
  return result


async def get_quiz(quiz_id: str):
  object_id = ObjectId(quiz_id)
  quiz = await collection.find_one({'_id': object_id})

  if quiz and '_id' in quiz:
    quiz['_id'] = str(quiz['_id'])

  return quiz


async def search_quizzes(
    user_id: Optional[str] = None,
    is_public: Optional[bool] = None,
    min_created_date: Optional[datetime] = None,
    max_created_date: Optional[datetime] = None,
    min_last_modified: Optional[datetime] = None,
    max_last_modified: Optional[datetime] = None,
    difficulty: Optional[str] = None,
    categories: Optional[List[str]] = None,
    size: Optional[int] = None,
    start: Optional[int] = None,
    title: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[int] = None
):
  query = {}

  if user_id is None:
    query['is_public'] = True
  else:
    query['user_id'] = user_id
    if is_public is not None:
      query['is_public'] = is_public

  if min_created_date or max_created_date:
    created_date_query = {}
    if min_created_date:
      created_date_query['$gte'] = min_created_date
    if max_created_date:
      created_date_query['$lte'] = max_created_date
    query['created_date'] = created_date_query

  if min_last_modified or max_last_modified:
    last_modified_query = {}
    if min_last_modified:
      last_modified_query['$gte'] = min_last_modified
    if max_last_modified:
      last_modified_query['$lte'] = max_last_modified
    query['last_modified_date'] = last_modified_query

  if difficulty:
    query['difficulty'] = difficulty

  if categories:
    query['categories'] = {'$in': categories}

  if title:
    query['title'] = {"$regex": title, "$options": "i"}

  projection = {'questions': 0}

  cursor = collection.find(query, projection)
  if sort_by is not None and sort_order is not None:
    sort_dict = {sort_by: sort_order}
    cursor = cursor.sort(sort_dict)
  if start is not None:
    cursor = cursor.skip(start)
  if size is not None:
    cursor = cursor.limit(size)

  results = await cursor.to_list(length=size)

  for doc in results:
    if '_id' in doc:
      doc['_id'] = str(doc['_id'])

  return results


async def count_quizzes(
    user_id: Optional[str] = None,
    is_public: Optional[bool] = None,
    min_created_date: Optional[datetime] = None,
    max_created_date: Optional[datetime] = None,
    min_last_modified: Optional[datetime] = None,
    max_last_modified: Optional[datetime] = None,
    difficulty: Optional[str] = None,
    categories: Optional[List[str]] = None,
    title: Optional[str] = None
) -> int:
  query = {}

  if user_id is None:
    query['is_public'] = True
  else:
    query['user_id'] = user_id
    if is_public is not None:
      query['is_public'] = is_public

  if min_created_date or max_created_date:
    query["created_date"] = {}
    if min_created_date:
      query["created_date"]["$gte"] = min_created_date
    if max_created_date:
      query["created_date"]["$lte"] = max_created_date

  if min_last_modified or max_last_modified:
    query["last_modified_date"] = {}
    if min_last_modified:
      query["last_modified_date"]["$gte"] = min_last_modified
    if max_last_modified:
      query["last_modified_date"]["$lte"] = max_last_modified

  if difficulty:
    query["difficulty"] = difficulty

  if categories:
    query["categories"] = {"$in": categories}

  if title:
    query["title"] = {"$regex": title, "$options": "i"}

  count = await collection.count_documents(query)
  return count
