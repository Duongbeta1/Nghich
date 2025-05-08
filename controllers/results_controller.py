from fastapi import APIRouter, HTTPException
from models.results import (
    add_result, update_result_answer, get_result,
    delete_result, get_results_by_quiz, get_results_by_user,
    count_results_by_quiz, count_results_by_user,
    update_result_answer_by_question
)
from bson import ObjectId
from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel
from pydantic import validator

router = APIRouter()


class ResultAnswerUpdate(BaseModel):
  question_index: int
  answer: int


class QuestionAnswerUpdate(BaseModel):
    question_id: str
    answer: int
    is_correct: bool

    @validator('answer')
    def validate_answer(cls, v):
        if v not in [0, 1, 2, 3]:
            raise ValueError('Answer must be between 0 and 3')
        return v


@router.post("/quiz/{quiz_id}/user/{user_id}")
async def create_result(quiz_id: str, user_id: str):
  try:
    ObjectId(quiz_id)
    result_id = await add_result(quiz_id, user_id)
    return {
        "status": "success",
        "data": str(result_id),
        "message": "Result created successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


# @router.put("/{result_id}/answer")
# async def update_answer_route(result_id: str, update_data: ResultAnswerUpdate):
#     try:
#         ObjectId(result_id)
#         updated_result = await update_result_answer(result_id, update_data.question_index, update_data.answer)
#         if updated_result:
#             return {
#                 "status": "success",
#                 "data": updated_result,
#                 "message": "Answer updated successfully"
#             }
#         else:
#             return {
#                 "status": "error",
#                 "message": "Failed to update answer"
#             }
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }


@router.get("/{result_id}")
async def get_result_route(result_id: str):
  try:
    ObjectId(result_id)
    result = await get_result(result_id)
    if result:
      return {
          "status": "success",
          "data": result,
          "message": "Result fetched successfully"
      }
    else:
      return {
          "status": "error",
          "message": "Result not found"
      }
  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


@router.get("/quiz/{quiz_id}")
async def get_results_by_quiz_route(
    quiz_id: str, 
    skip: Optional[int] = None, 
    limit: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[int] = None
):
  try:
    ObjectId(quiz_id)
    results = await get_results_by_quiz(quiz_id, skip, limit, sort_by, sort_order)
    return {
        "status": "success",
        "data": results,
        "total": len(results),
        "message": "Results fetched successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


@router.get("/user/{user_id}")
async def get_results_by_user_route(
    user_id: str, 
    skip: Optional[int] = None, 
    limit: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[int] = None
):
  try:
    results = await get_results_by_user(user_id, skip, limit, sort_by, sort_order)
    return {
        "status": "success",
        "data": results,
        "total": len(results),
        "message": "Results fetched successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


@router.get("/quiz/{quiz_id}/count")
async def count_results_by_quiz_route(quiz_id: str):
  try:
    ObjectId(quiz_id)
    total = await count_results_by_quiz(quiz_id)
    return {
        "status": "success",
        "count": total,
        "message": "Results count fetched successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


@router.get("/user/{user_id}/count")
async def count_results_by_user_route(user_id: str):
  try:
    total = await count_results_by_user(user_id)
    return {
        "status": "success",
        "count": total,
        "message": "Results count fetched successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


@router.delete("/{result_id}")
async def delete_result_route(result_id: str):
  try:
    ObjectId(result_id)
    result = await delete_result(result_id)
    if result.deleted_count == 0:
      return {
          "status": "error",
          "message": "Result not found"
      }
    return {
        "status": "success",
        "message": "Result deleted successfully"
    }
  except Exception as e:
    return {
        "status": "error",
        "message": str(e)
    }


@router.put("/{result_id}/answer")
async def update_question_answer_route(result_id: str, update_data: QuestionAnswerUpdate):
    try:
        ObjectId(result_id)
        ObjectId(update_data.question_id)
        
        updated_result = await update_result_answer_by_question(
            result_id=result_id,
            question_id=update_data.question_id,
            answer=update_data.answer,
            is_correct=update_data.is_correct
        )
        
        if not updated_result:
            return {
                "status": "error",
                "message": "Failed to update answer"
            }
            
        return {
            "status": "success",
            "data": updated_result,
            "message": "Answer updated successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
