from models.mongo import mongo_database
from bson import ObjectId
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from models.quizzes import get_quiz

collection = mongo_database['results']


async def add_result(quiz_id: str, user_id: str):
  quiz = await get_quiz(quiz_id)

  if not quiz:
    raise ValueError(f"Quiz with id {quiz_id} not found")

  num_questions = len(quiz.get('questions', []))
  
  # Create status array with question_id and initial answer
  status = []
  for question in quiz.get('questions', []):
    print(question)
    status.append({
      "question_id": question["question_id"],
      "answer": -1,
      "is_correct": False
    })

  result = {
      'quiz_id': quiz_id,
      'user_id': user_id,
      'num_unfinished': num_questions,
      'num_correct': 0,
      'num_incorrect': 0,
      'status': status,
      'created_date': datetime.now(timezone.utc),
      'last_modified_date': datetime.now(timezone.utc)
  }

  existing_result = await collection.find_one({
      'quiz_id': quiz_id,
      'user_id': user_id
  })

  if existing_result:
    return existing_result['_id']

  result_id = await collection.insert_one(result)
  return result_id.inserted_id


async def update_result_answer_by_question(result_id: str, question_id: str, answer: int, is_correct: bool):
  try:
    object_id = ObjectId(result_id)
    result = await collection.find_one({'_id': object_id})
    
    if not result:
      raise ValueError(f"Result with id {result_id} not found")
    
    # Find and update the answer for the specific question
    status = result['status']
    found = False
    old_answer = None
    old_is_correct = None
    
    for item in status:
      if str(item['question_id']) == question_id:
        old_answer = item['answer']
        old_is_correct = item['is_correct']
        item['answer'] = answer
        item['is_correct'] = is_correct
        found = True
        break
    
    if not found:
      raise ValueError(f"Question with id {question_id} not found in result")
    
    # Update counters
    update_data = {
      'status': status,
      'last_modified_date': datetime.now(timezone.utc)
    }
    
    if old_answer == -1:
      # First time answering this question
      update_data['num_unfinished'] = result['num_unfinished'] - 1
      if is_correct:
        update_data['num_correct'] = result['num_correct'] + 1
      else:
        update_data['num_incorrect'] = result['num_incorrect'] + 1
    elif old_is_correct != is_correct:
      # Answer correctness changed
      if is_correct:
        update_data['num_correct'] = result['num_correct'] + 1
        update_data['num_incorrect'] = result['num_incorrect'] - 1
      else:
        update_data['num_correct'] = result['num_correct'] - 1
        update_data['num_incorrect'] = result['num_incorrect'] + 1
    
    # Update the document with the new status array
    await collection.update_one(
      {'_id': object_id},
      {'$set': update_data}
    )
    
    # Return updated document
    return await get_result(result_id)
  except Exception as e:
    raise Exception(f"Error updating result answer: {str(e)}")


async def update_result_answer(result_id: str, question_index: int, answer: int):
  object_id = ObjectId(result_id)
  result = await collection.find_one({'_id': object_id})

  if not result:
    raise ValueError(f"Result with id {result_id} not found")

  quiz_id = result['quiz_id']
  quiz_collection = mongo_database['quizzes']
  quiz = await quiz_collection.find_one({'_id': ObjectId(quiz_id)})

  if not quiz:
    raise ValueError(f"Quiz with id {quiz_id} not found")

  if question_index >= len(quiz['questions']):
    raise ValueError(f"Question index {question_index} out of range")

  correct_answer = quiz['questions'][question_index]['answer']
  status = result['status'].copy()

  # Update statistics based on previous and new answer
  old_answer = status[question_index]
  status[question_index] = answer

  update_data = {
      'status': status,
      'last_modified_date': datetime.now(timezone.utc)
  }

  # Update counters based on the change
  if old_answer == -1:  # Previously unanswered
    update_data['num_unfinished'] = result['num_unfinished'] - 1
    if answer == correct_answer:
      update_data['num_correct'] = result['num_correct'] + 1
    else:
      update_data['num_incorrect'] = result['num_incorrect'] + 1
  elif old_answer == correct_answer and answer != correct_answer:  # Changed from correct to incorrect
    update_data['num_correct'] = result['num_correct'] - 1
    update_data['num_incorrect'] = result['num_incorrect'] + 1
  elif old_answer != correct_answer and answer == correct_answer:  # Changed from incorrect to correct
    update_data['num_correct'] = result['num_correct'] + 1
    update_data['num_incorrect'] = result['num_incorrect'] - 1

  await collection.update_one({'_id': object_id}, {'$set': update_data})
  return await collection.find_one({'_id': object_id})


async def get_result(result_id: str):
  object_id = ObjectId(result_id)
  result = await collection.find_one({'_id': object_id})

  if result:
    result['_id'] = str(result['_id'])

  return result


async def delete_result(result_id: str):
  object_id = ObjectId(result_id)
  result = await collection.delete_one({'_id': object_id})
  return result


async def get_results_by_quiz(quiz_id: str, skip: Optional[int] = None, limit: Optional[int] = None, sort_by: Optional[str] = None, sort_order: Optional[int] = None):
  cursor = collection.find({'quiz_id': quiz_id})
  
  # Apply sorting if specified
  if sort_by is not None and sort_order is not None:
    sort_dict = {sort_by: sort_order}
    cursor = cursor.sort(sort_dict)
  
  # Apply pagination if specified
  if skip is not None:
    cursor = cursor.skip(skip)
  if limit is not None:
    cursor = cursor.limit(limit)
    
  results = await cursor.to_list(length=None)

  for result in results:
    result['_id'] = str(result['_id'])

  return results


async def get_results_by_user(user_id: str, skip: Optional[int] = None, limit: Optional[int] = None, sort_by: Optional[str] = None, sort_order: Optional[int] = None):
  cursor = collection.find({'user_id': user_id})
  
  # Apply sorting if specified
  if sort_by is not None and sort_order is not None:
    sort_dict = {sort_by: sort_order}
    cursor = cursor.sort(sort_dict)
  
  # Apply pagination if specified
  if skip is not None:
    cursor = cursor.skip(skip)
  if limit is not None:
    cursor = cursor.limit(limit)
    
  results = await cursor.to_list(length=None)

  for result in results:
    result['_id'] = str(result['_id'])

  return results


async def delete_results_by_quiz(quiz_id: str):
  return await collection.delete_many({'quiz_id': quiz_id})


async def update_results_for_quiz_edit(quiz_id: str, old_quiz: Dict[str, Any], new_quiz: Dict[str, Any]):
  # Get all results for this quiz
  results = await collection.find({'quiz_id': quiz_id}).to_list(length=1000)

  old_questions = old_quiz.get('questions', [])
  new_questions = new_quiz.get('questions', [])

  # If question count changed, we need to adjust all results
  if len(old_questions) != len(new_questions):
    for result in results:
      old_status = result['status']
      # Create new status array with appropriate length
      new_status = [-1] * len(new_questions)

      # Copy answers for questions that still exist
      for i in range(min(len(old_status), len(new_status))):
        new_status[i] = old_status[i]

      # Recalculate statistics
      num_unfinished = new_status.count(-1)
      num_correct = 0
      num_incorrect = 0

      for i, answer in enumerate(new_status):
        if answer != -1:
          if answer == new_questions[i]['answer']:
            num_correct += 1
          else:
            num_incorrect += 1

      # Update the result
      await collection.update_one(
          {'_id': result['_id']},
          {'$set': {
              'status': new_status,
              'num_unfinished': num_unfinished,
              'num_correct': num_correct,
              'num_incorrect': num_incorrect,
              'last_modified_date': datetime.now(timezone.utc)
          }}
      )
  else:
    # Only need to check for answer changes
    changed_answers = []
    for i, (old_q, new_q) in enumerate(zip(old_questions, new_questions)):
      if old_q.get('answer') != new_q.get('answer'):
        changed_answers.append((i, new_q.get('answer')))

    # Update results if any answers changed
    if changed_answers:
      for result in results:
        updates_needed = False
        status = result['status']
        num_correct = result['num_correct']
        num_incorrect = result['num_incorrect']

        for idx, new_answer in changed_answers:
          if status[idx] != -1:  # If question was answered
            old_was_correct = status[idx] == old_questions[idx]['answer']
            new_is_correct = status[idx] == new_answer

            if old_was_correct and not new_is_correct:
              num_correct -= 1
              num_incorrect += 1
              updates_needed = True
            elif not old_was_correct and new_is_correct:
              num_correct += 1
              num_incorrect -= 1
              updates_needed = True

        if updates_needed:
          await collection.update_one(
              {'_id': result['_id']},
              {'$set': {
                  'num_correct': num_correct,
                  'num_incorrect': num_incorrect,
                  'last_modified_date': datetime.now(timezone.utc)
              }}
          )


async def count_results_by_quiz(quiz_id: str) -> int:
  return await collection.count_documents({'quiz_id': quiz_id})


async def count_results_by_user(user_id: str) -> int:
  return await collection.count_documents({'user_id': user_id})
