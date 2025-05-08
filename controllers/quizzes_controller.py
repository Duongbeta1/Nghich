from fastapi import APIRouter, BackgroundTasks, HTTPException
from models.quizzes import update_quiz, delete_quiz, search_quizzes, count_quizzes, get_quiz
from bson import ObjectId
from typing import Dict, Optional, List
from datetime import datetime, time
from pydantic import BaseModel, validator
from controllers.shared_resources import task_semaphore, task_results
import uuid

router = APIRouter()


class SearchQuery(BaseModel):
  user_id: Optional[str] = None
  is_public: Optional[bool] = None
  min_created_date: Optional[str] = None
  max_created_date: Optional[str] = None
  min_last_modified: Optional[str] = None
  max_last_modified: Optional[str] = None
  difficulty: Optional[str] = None
  categories: Optional[List[str]] = None
  size: Optional[int] = None
  start: Optional[int] = None
  title: Optional[str] = None
  sort_by: Optional[str] = "created_date"
  sort_order: Optional[int] = -1

  @validator('min_created_date', 'max_created_date', 'min_last_modified', 'max_last_modified')
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
  #   if v not in ["created_date", "num_question", "last_modified_date"]:
  #     raise ValueError(
  #         "sort_by must be either 'created_date' or 'num_question' or 'last_modified_date'")
  #   return v

  @validator('sort_order')
  def validate_sort_order(cls, v):
    if v not in [-1, 1]:
      raise ValueError(
          "sort_order must be either -1 (descending) or 1 (ascending)")
    return v

  def model_post_init(self, __context):
    if self.max_created_date:
      self.max_created_date = self.max_created_date.replace(
          hour=23, minute=59, second=59)
    if self.max_last_modified:
      self.max_last_modified = self.max_last_modified.replace(
          hour=23, minute=59, second=59)


@router.put("/{quiz_id}")
async def update_quiz_direct(quiz_id: str, quiz_data: Dict):
  try:
    ObjectId(quiz_id)
    result = await update_quiz(quiz_id, quiz_data)
    if result.modified_count == 0:
      return {"status": "error", "message": "Quiz not found"}
    return {"status": "success", "message": "Quiz updated successfully"}
  except Exception as e:
    return {"status": "error", "message": str(e)}


@router.delete("/{quiz_id}")
async def delete_quiz_direct(quiz_id: str):
  try:
    ObjectId(quiz_id)
    result = await delete_quiz(quiz_id)
    if result.deleted_count == 0:
      return {"status": "error", "success": False, "message": "Quiz not found"}
    return {"status": "success", "success": True, "message": "Quiz deleted successfully"}
  except Exception as e:
    return {"status": "error", "success": False, "message": str(e)}


@router.get("/{quiz_id}")
async def get_quiz_direct(quiz_id: str):
  try:
    ObjectId(quiz_id)
    quiz = await get_quiz(quiz_id)
    if not quiz:
      return {"status": "error", "message": "Quiz not found"}
    return {"status": "success", "data": quiz, "message": "Quiz fetched successfully"}
  except Exception as e:
    return {"status": "error", "message": str(e)}


@router.post("/search")
async def search_quizzes_direct(query: SearchQuery):
  try:
    results = await search_quizzes(
        user_id=query.user_id,
        is_public=query.is_public,
        min_created_date=query.min_created_date,
        max_created_date=query.max_created_date,
        min_last_modified=query.min_last_modified,
        max_last_modified=query.max_last_modified,
        difficulty=query.difficulty,
        categories=query.categories,
        size=query.size,
        start=query.start,
        title=query.title,
        sort_by=query.sort_by,
        sort_order=query.sort_order
    )
    return {
        "status": "success",
        "data": results,
        "total": len(results),
        "message": "Quizzes fetched successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "data": [],
        "total": 0,
        "message": str(e)
    }


@router.post("/count")
async def count_quizzes_direct(query: SearchQuery):
  try:
    count = await count_quizzes(
        user_id=query.user_id,
        is_public=query.is_public,
        min_created_date=query.min_created_date,
        max_created_date=query.max_created_date,
        min_last_modified=query.min_last_modified,
        max_last_modified=query.max_last_modified,
        difficulty=query.difficulty,
        categories=query.categories,
        title=query.title
    )
    return {
        "status": "success",
        "count": count,
        "message": "Count completed successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "count": 0,
        "message": str(e)
    }
