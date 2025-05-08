from fastapi import APIRouter, UploadFile, File
from models.documents import add_doc_with_link, get_document, search_documents, count_documents, delete_document, update_document
from service.processors.service import delete_chunks, process_pdf, process_docx, process_text_file, add_document
import os
import uuid
import tempfile
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, validator
import httpx

router = APIRouter()


class SearchQuery(BaseModel):
  user_id: Optional[str] = None
  is_public: Optional[bool] = None
  min_date: Optional[str] = None
  max_date: Optional[str] = None
  filename: Optional[str] = None
  file_extension: Optional[str] = None
  size: Optional[int] = None
  start: Optional[int] = None
  sort_by: Optional[str] = None
  sort_order: Optional[int] = None

  @validator('min_date', 'max_date')
  def parse_date(cls, v):
    if v is None:
      return None
    try:
      date_obj = datetime.strptime(v, '%d/%m/%Y')
      return date_obj
    except ValueError:
      raise ValueError('Date must be in dd/mm/yyyy format')

  # @validator('sort_by')
  # def validate_sort_by(cls, v):
  #   if v is not None and v not in ["date"]:
  #     raise ValueError("sort_by must be 'date'")
  #   return v

  @validator('sort_order')
  def validate_sort_order(cls, v):
    if v is not None and v not in [-1, 1]:
      raise ValueError(
          "sort_order must be either -1 (descending) or 1 (ascending)")
    return v

  def model_post_init(self, __context):
    if self.max_date:
      self.max_date = self.max_date.replace(hour=23, minute=59, second=59)


@router.post("/document/search")
async def search_documents_route(query: SearchQuery):
  try:
    results = await search_documents(
        user_id=query.user_id,
        is_public=query.is_public,
        min_date=query.min_date,
        max_date=query.max_date,
        filename=query.filename,
        file_extension=query.file_extension,
        size=query.size,
        start=query.start,
        sort_by=query.sort_by,
        sort_order=query.sort_order
    )

    return {
        "status": "success",
        "data": results,
        "total": len(results),
        "message": "Documents fetched successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "data": [],
        "total": 0,
        "message": str(e)
    }


@router.post("/document/count")
async def count_documents_route(query: SearchQuery):
  try:
    total = await count_documents(
        user_id=query.user_id,
        is_public=query.is_public,
        min_date=query.min_date,
        max_date=query.max_date,
        filename=query.filename,
        file_extension=query.file_extension
    )

    return {
        "status": "success",
        "count": total,
        "message": "Count fetched successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "count": 0,
        "message": str(e)
    }


@router.get("/document/{document_id}")
async def get_document_route(document_id: str):
  try:
    document = await get_document(document_id)
    if not document:
      return {
          "status": "error",
          "data": {},
          "message": "Document not found"
      }

    return {
        "status": "success",
        "data": document,
        "message": "Document fetched successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "data": {},
        "message": str(e)
    }


@router.delete("/document/{document_id}")
async def delete_document_route(document_id: str):
  try:
    await delete_chunks(document_id)
    success = await delete_document(document_id)

    if not success:
      return {
          "status": "error",
          "message": "Document not found"
      }

    return {
        "status": "success",
        "message": "Document and its chunks deleted successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


async def download_document_file(document_id: str):
  document = await get_document(document_id)
  if not document:
    return None, "Document not found"

  headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
  }

  async with httpx.AsyncClient(
      timeout=httpx.Timeout(300.0),
      follow_redirects=True
  ) as client:
    print(f'Downloading file from url={document["file_url"]}')
    print(headers)

    async with client.stream('GET', document['file_url'], headers=headers) as response:
      if response.status_code != 200:
        return None, "Failed to download file from URL"

      file_ext = document['file_extension']
      with tempfile.NamedTemporaryFile(delete=False, suffix='.'+file_ext) as tmp:
        temp_file_path = tmp.name
        async for chunk in response.aiter_bytes():
          tmp.write(chunk)
        tmp.flush()

  print('Download successfully')
  return temp_file_path, document['file_extension']


@router.post("/document/pinecone/{document_id}")
async def reprocess_to_pinecone(document_id: str):
  try:
    temp_file_path, file_ext = await download_document_file(document_id)
    if not temp_file_path:
      return {
          "status": "error",
          "message": file_ext
      }

    print('Processing file')

    try:
      if file_ext == 'pdf':
        documents = await process_pdf(temp_file_path)
      elif file_ext in ['docx', 'doc']:
        documents = await process_docx(temp_file_path)
      elif file_ext in ['md', 'txt']:
        documents = await process_text_file(temp_file_path)
      else:
        raise ValueError(f"Unsupported file type: {file_ext}")

      print('Processing successfully')

      document = await get_document(document_id)
      await add_document(
          documents,
          document['user_id'],
          document['is_public'],
          document_id,
          document['filename']
      )

      print('Adding to Pinecone')

      return {
          "status": "success",
          "message": f"Successfully reprocessed {len(documents)} documents into Pinecone"
      }

    finally:
      if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


@router.post("/upload")
async def upload_document(
    user_id: str,
    is_public: bool,
    file: UploadFile = File(...)
):
  try:
    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
      temp_file_path = tmp.name
      content = await file.read()
      tmp.write(content)

    result = await add_doc_with_link(
        user_id=user_id,
        is_public=is_public,
        filename=file.filename,
        file_path=temp_file_path,
    )

    os.remove(temp_file_path)

    document = await get_document(str(result.inserted_id))

    return {
        "status": "success",
        "data": document,
        "message": "File uploaded successfully"
    }

  except Exception as e:
    if os.path.exists(temp_file_path):
      os.remove(temp_file_path)

    return {
        "status": "error",
        "message": str(e)
    }


@router.get("/documents")
async def list_documents(
    user_id: str,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_date",
    sort_order: int = -1
):
  try:
    if sort_by not in ["created_date", "questions_count"]:
      raise ValueError(
          "sort_by must be either 'created_date' or 'questions_count'")
    if sort_order not in [-1, 1]:
      raise ValueError(
          "sort_order must be either -1 (descending) or 1 (ascending)")

    documents = await list_user_documents(
        user_id=user_id,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return {
        "status": "success",
        "data": documents,
        "message": "Documents fetched successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "data": [],
        "message": str(e)
    }


@router.put("/document")
async def update_document_route(document_id: str, filename: Optional[str] = None, is_public: Optional[bool] = None):
    try:
        updated_document = await update_document(document_id, filename, is_public)
        
        if not updated_document:
            return {
                "status": "error",
                "message": "Document not found or no changes made"
            }
            
        return {
            "status": "success",
            "data": updated_document,
            "message": "Document updated successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
