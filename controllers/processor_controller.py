from fastapi import APIRouter, Form, UploadFile, BackgroundTasks
from controllers.shared_resources import task_semaphore, task_results
from typing import Annotated
from service.processors.service import query_document, process_pdf, process_docx, process_text_file, add_document
from service.generators.base import upload_file
from models.documents import add_document as save_document_info
from models.documents import add_doc_with_link

import os
import tempfile
import uuid

router = APIRouter()


@router.post("/add")
async def add_doc(file: UploadFile, user_id: str, is_public: bool, background_tasks: BackgroundTasks, mode: str = "text"):
  filename = file.filename
  file_ext = os.path.splitext(filename)[1].lower()

  with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
    temp_file_path = tmp.name
    content = await file.read()
    tmp.write(content)

  task_id = str(uuid.uuid4())

  background_tasks.add_task(
      process_file, temp_file_path, user_id, is_public, file_ext, task_id, mode, filename)

  return {"task_id": task_id, "status": "processing"}


# @router.post("/upload")
# async def upload_doc(file: UploadFile, user_id: str, is_public: bool, background_tasks: BackgroundTasks):
#   filename = file.filename
#   file_ext = os.path.splitext(filename)[1].lower()

#   with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
#     temp_file_path = tmp.name
#     content = await file.read()
#     tmp.write(content)

#   task_id = str(uuid.uuid4())
#   background_tasks.add_task(
#       process_upload_file, temp_file_path, user_id, is_public, filename, task_id)

#   return {"task_id": task_id, "status": "processing"}


@router.post("/query")
async def query(user_id: Annotated[str, Form()], query_text: Annotated[str, Form()], background_tasks: BackgroundTasks):
  task_id = str(uuid.uuid4())
  background_tasks.add_task(get_query_result, query_text, user_id, task_id)
  return {"task_id": task_id, "status": "processing"}


async def get_query_result(query_text: str, user_id: str, task_id):
  try:
    async with task_semaphore:
      task_results[task_id] = {"status": "processing"}
      resp = await query_document(query_text, user_id)

      task_results[task_id] = {
          "status": "completed",
          "message": resp.__str__()
      }

  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}


# async def process_upload_file(temp_file_path, user_id, is_public, filename, task_id):
#   try:
#     async with task_semaphore:
#       task_results[task_id] = {"status": "uploading"}

#       file_url = await upload_file(temp_file_path)
#       await save_document_info(user_id, is_public, filename, file_url)

#       task_results[task_id] = {
#           "status": "completed",
#           "message": f"Uploaded file {filename} successfully",
#           "file_url": file_url
#       }
#   except Exception as e:
#     import traceback
#     traceback.print_exc()
#     task_results[task_id] = {"status": "error", "message": str(e)}
#   finally:
#     if os.path.exists(temp_file_path):
#       os.remove(temp_file_path)


async def process_file(temp_file_path, user_id, is_public, file_ext, task_id, mode="text", filename=None):
  try:
    async with task_semaphore:

      print(f'Adding document {temp_file_path} of {user_id}')

      task_results[task_id] = {"status": "uploading"}

      insert_result = await add_doc_with_link(user_id, is_public, filename, temp_file_path)
      document_id = str(insert_result.inserted_id)

      print(f'Insert {document_id} into MongoDB')

      task_results[task_id] = {"status": "processing",
                               "message": f"Processing file {filename}..."}

      if file_ext == '.pdf':
        documents = await process_pdf(temp_file_path, mode)
      elif file_ext in ['.docx', '.doc']:
        documents = await process_docx(temp_file_path)
      elif file_ext in ['.md', '.txt']:
        documents = await process_text_file(temp_file_path)
      else:
        raise ValueError(f"Unsupported file type: {file_ext}")

      await add_document(documents, user_id, is_public, document_id, filename)

      task_results[task_id] = {
          "status": "completed",
          "message": f"Successfully processed {len(documents)} documents",
      }
  except Exception as e:
    import traceback
    traceback.print_exc()
    task_results[task_id] = {"status": "error", "message": str(e)}
  finally:
    if os.path.exists(temp_file_path):
      os.remove(temp_file_path)
