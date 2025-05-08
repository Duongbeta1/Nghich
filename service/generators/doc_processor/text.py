from service.generators.generators import DocumentProcessor
from llama_index.core import SimpleDirectoryReader
from controllers.shared_resources import task_results


class TextFileProcessor(DocumentProcessor):
  def get_text(self, file_path):
    reader = SimpleDirectoryReader(input_files=[file_path])
    document = reader.load_data()[0]

    return document.get_content()

  async def generate_questions(self, file_path: str, num_question: int, language: str, task_id: str = None, difficulty: str = "medium"):
    try:
      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Reading text file"
        }

      text = self.get_text(file_path)

      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Generating questions from text"
        }

      return await self.text_processor.generate_questions(text, num_question, language, difficulty)

    except Exception as e:
      if task_id:
        task_results[task_id] = {
            "status": "error",
            "message": str(e)
        }
      raise e

  async def generate_questions_from_text(self, text: str, num_question: int, language: str, task_id: str = None, difficulty: str = "medium"):
    try:
      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Generating questions from text"
        }

      questions = await self.text_processor.generate_questions(text, num_question, language, difficulty)

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
            "message": str(e)
        }
      raise e
