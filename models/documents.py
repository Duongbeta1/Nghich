from models.mongo import mongo_database
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional
import os
from service.generators.base import upload_file


collection = mongo_database['documents']


async def add_document(user_id: str, is_public: bool, filename: str, file_url: str, file_size: int, file_extension: str):
  document = {
      'user_id': user_id,
      'is_public': is_public,
      'filename': filename,
      'file_url': file_url,
      'file_size': file_size,
      'file_extension': file_extension,
      'date': datetime.now(timezone.utc),
  }
  return await collection.insert_one(document)


async def add_doc_with_link(user_id: str, is_public: bool, filename: str, file_path: str):
  file_url = await upload_file(file_path)
  file_size = os.path.getsize(file_path)  # size in bytes
  file_extension = os.path.splitext(file_path)[1]

  filename = filename.replace(file_extension, '')
  file_extension = file_extension.replace('.', '')
  print(f'Adding {filename} {file_extension} to MongoDB')
  return await add_document(
      user_id=user_id,
      is_public=is_public,
      filename=filename,
      file_url=file_url,
      file_size=file_size,
      file_extension=file_extension
  )


async def get_document(document_id: str):
  object_id = ObjectId(document_id)
  document = await collection.find_one({'_id': object_id})

  if document and '_id' in document:
    document['_id'] = str(document['_id'])

  return document


async def delete_document(document_id: str):
  try:
    object_id = ObjectId(document_id)
    result = await collection.delete_one({'_id': object_id})
    return result.deleted_count > 0
  except Exception as e:
    raise Exception(f"Error deleting document: {str(e)}")


async def search_documents(
    user_id: Optional[str] = None,
    is_public: Optional[bool] = None,
    min_date: Optional[datetime] = None,
    max_date: Optional[datetime] = None,
    filename: Optional[str] = None,
    file_extension: Optional[str] = None,
    size: Optional[int] = None,
    start: Optional[int] = None,
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

  if min_date or max_date:
    date_query = {}
    if min_date:
      date_query['$gte'] = min_date
    if max_date:
      date_query['$lte'] = max_date
    query['date'] = date_query

  if filename:
    query['filename'] = {'$regex': filename, '$options': 'i'}

  if file_extension:
    query['file_extension'] = {
        '$regex': f'^{file_extension}$', '$options': 'i'}

  cursor = collection.find(query)

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


async def count_documents(
    user_id: Optional[str] = None,
    is_public: Optional[bool] = None,
    min_date: Optional[datetime] = None,
    max_date: Optional[datetime] = None,
    filename: Optional[str] = None,
    file_extension: Optional[str] = None
) -> int:
  query = {}

  if user_id is None:
    query['is_public'] = True
  else:
    query['user_id'] = user_id
    if is_public is not None:
      query['is_public'] = is_public

  if min_date or max_date:
    query['date'] = {}
    if min_date:
      query['date']['$gte'] = min_date
    if max_date:
      query['date']['$lte'] = max_date

  if filename:
    query['filename'] = {'$regex': filename, '$options': 'i'}

  if file_extension:
    query['file_extension'] = {
        '$regex': f'^{file_extension}$', '$options': 'i'}

  count = await collection.count_documents(query)
  return count


async def update_document(document_id: str, filename: Optional[str] = None, is_public: Optional[bool] = None):
  try:
    object_id = ObjectId(document_id)
    update_data = {}
    
    if filename is not None:
      update_data['filename'] = filename
    if is_public is not None:
      update_data['is_public'] = is_public
      
    if not update_data:
      raise Exception("No fields to update")
      
    result = await collection.update_one(
      {'_id': object_id},
      {'$set': update_data}
    )
    
    if result.modified_count == 0:
      return None
      
    updated_document = await get_document(document_id)
    return updated_document
  except Exception as e:
    raise Exception(f"Error updating document: {str(e)}")
