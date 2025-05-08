import asyncio
from fastapi import APIRouter

router = APIRouter()

MAX_CONCURRENT_TASKS = 3
task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)


@router.get("/status/{task_id}")
async def get_status(task_id: str):
  if task_id in task_results:
    return task_results[task_id]
  return {"status": "not_found"}

task_results = {}
