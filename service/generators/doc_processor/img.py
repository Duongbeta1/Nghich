from service.generators.generators import DocumentProcessor, ImageProcessor
from PIL import Image
import base64
import io
import asyncio
from controllers.shared_resources import task_results


class ImageGenerator(DocumentProcessor):
  def __init__(self, image_processor: ImageProcessor):
    self.image_processor = image_processor

  def img_to_base64(self, img_path: str, task_id: str = None):
    try:
      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": f"Converting image to base64"
        }

      # Open and convert image to base64
      with Image.open(img_path) as img:
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Image converted successfully"
        }

      return base64_image

    except Exception as e:
      if task_id:
        task_results[task_id] = {
            "status": "error",
            "message": f"Error converting image: {str(e)}"
        }
      raise e

  async def generate_questions(self, img_path: str, num_question: int, language: str, task_id: str = None, difficulty: str = "medium"):
    try:
      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Converting image to base64"
        }

      # Convert image to base64
      base64_image = await asyncio.to_thread(self.img_to_base64, img_path, task_id)

      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Generating questions from image"
        }

      # Generate questions using the image processor
      questions = await self.image_processor.generate_questions([base64_image], num_question, language, difficulty)

      if task_id:
        task_results[task_id] = {
            "status": "completed",
            "message": "Questions generated successfully"
        }

      return questions

    except Exception as e:
      if task_id:
        task_results[task_id] = {
            "status": "error",
            "message": f"Error generating questions: {str(e)}"
        }
      raise e
