from service.generators.generators import DocumentProcessor, TextProcessor, ImageProcessor, FileProcessor
from service.generators.base import FileUploader
import fitz
from PIL import Image
import base64
import io
import asyncio
from controllers.shared_resources import task_results


class PDFProcessor(DocumentProcessor):
  def __init__(self, text_processor: TextProcessor, image_processor: ImageProcessor, file_processor: FileProcessor, file_uploader: FileUploader):
    self.text_processor = text_processor
    self.image_processor = image_processor
    self.file_processor = file_processor
    self.file_uploader = file_uploader

  # https://python.langchain.com/docs/how_to/document_loader_pdf/#use-of-multimodal-models
  def pdf_to_base64(self, pdf_path: str, task_id: str = None):
    pages = []
    with fitz.open(pdf_path) as pdf_document:
      total_pages = pdf_document.page_count

      for page_number in range(total_pages):
        if task_id:
          task_results[task_id] = {
              "status": "processing",
              "progress": f"Processing page {page_number + 1}/{total_pages}"
          }

        page = pdf_document.load_page(page_number)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        pages.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))
        # print(page_number, ':', len(pages[-1]))

    return pages

  def pdf_to_text(self, pdf_path: str, task_id: str = None):
    text = ""
    with fitz.open(pdf_path) as doc:
      total_pages = len(doc)
      for page_num in range(total_pages):
        if task_id:
          task_results[task_id] = {
              "status": "processing",
              "progress": f"Processing page {page_num + 1}/{total_pages}"
          }
        page = doc[page_num]
        text += page.get_text()
    return text

  async def generate_questions(self, pdf_path: str, num_question: int, language: str, task_id: str = None, difficulty: str = "medium"):
    with fitz.open(pdf_path) as doc:
      total_pages = len(doc)
      if total_pages > 300:
        if task_id:
          task_results[task_id] = {
              "status": "failed", "progress": f"PDF with {total_pages} exceeds our limit"}
        return {}
    if task_id:
      task_results[task_id] = {"status": "processing",
                               "progress": f"Generating questions from {pdf_path}"}
    genai_link = await self.file_uploader.upload_pdf(pdf_path)
    return await self.file_processor.generate_questions(genai_link, num_question, language, difficulty)

  async def generate_questions_from_images(self, pdf_path: str, num_question: int, language: str, task_id: str = None, difficulty: str = "medium"):
    base64_pages = await asyncio.to_thread(self.pdf_to_base64, pdf_path, task_id)
    if task_id:
      task_results[task_id] = {"status": "processing",
                               "progress": "Generating questions from images"}
    return await self.image_processor.generate_questions(base64_pages, num_question, language, difficulty)

  async def generate_questions_from_text(self, pdf_path: str, num_question: int, language: str, task_id: str = None, difficulty: str = "medium"):
    text = await asyncio.to_thread(self.pdf_to_text, pdf_path, task_id)
    if task_id:
      task_results[task_id] = {"status": "processing",
                               "progress": "Generating questions from text"}
    return await self.text_processor.generate_questions(text, num_question, language, difficulty)
