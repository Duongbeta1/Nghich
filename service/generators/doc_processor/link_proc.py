from service.generators.generators import DocumentProcessor, TextProcessor
from llama_index.readers.web import SimpleWebPageReader
from controllers.shared_resources import task_results


class LinkGenerator(DocumentProcessor):
  def __init__(self, text_processor: TextProcessor):
    self.text_processor = text_processor

  def get_text(self, url: str):
    try:
      reader = SimpleWebPageReader()
      documents = reader.load_data(urls=[url])
      if not documents or len(documents) == 0:
        raise Exception("Could not fetch content from the provided URL")
      return documents[0].get_content()
    except Exception as e:
      raise Exception(f"Error fetching web page content: {str(e)}")

  async def generate_questions(self, url: str, num_question: int, language: str, task_id: str = None, difficulty: str = "medium"):
    try:
      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Fetching web page content"
        }

      text = self.get_text(url)

      if task_id:
        task_results[task_id] = {
            "status": "processing",
            "progress": "Generating questions from web content"
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
