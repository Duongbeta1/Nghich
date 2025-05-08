import os
from service.generators.base import FileUploader, GenAIClient
from service.generators.generators import default_prompt, QuestionGenerator, TextProcessor, ImageProcessor, FileProcessor
from service.generators.summarizer import Summarizer
from service.generators.doc_processor.docx import DOCXProcessor
from service.generators.doc_processor.pdf import PDFProcessor
from service.generators.doc_processor.text import TextFileProcessor
from service.generators.doc_processor.img import ImageGenerator
from service.generators.doc_processor.link_proc import LinkGenerator

api_key = os.environ.get('GOOGLE_GENAI_KEY')

file_uploader = FileUploader(api_key=api_key)
generator = QuestionGenerator(api_key=api_key, default_prompt=default_prompt)
summarizer = Summarizer(api_key=api_key)
text_processor = TextProcessor(generator)
image_processor = ImageProcessor(generator, summarizer, text_processor)
file_processor = FileProcessor(generator)
pdf_processor = PDFProcessor(
    text_processor, image_processor, file_processor, file_uploader)
txt_file_processor = TextFileProcessor(
    text_processor, image_processor, file_processor)
doc_processor = DOCXProcessor(text_processor, image_processor, file_processor)
image_generator = ImageGenerator(image_processor)
link_generator = LinkGenerator(text_processor)
category_client = GenAIClient(api_key=api_key)
