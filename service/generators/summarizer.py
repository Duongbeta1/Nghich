import base64
from service.generators.base import GenAIClient


class Summarizer(GenAIClient):
  async def summarize_images(self, images):
    prompt = f'''
Can you provide a comprehensive summary of these given images? The summary should cover all the key points and main ideas presented in the original text, while also condensing the information into a concise and easy-to-understand format. Please ensure that the summary includes relevant details and examples that support the main ideas, while avoiding any unnecessary information or repetition. The length of the summary should be appropriate for the length and complexity of the original text, providing a clear and accurate overview without omitting any important information.
Just return the summary without any other text.
'''
    contents = [prompt]
    for image in images:
      contents.append({
          "mime_type": "image/jpeg",
          "data": base64.b64decode(image)
      })
    # TODO: Replace with generate_content_async
    resp = await self.model.generate_content_async(contents=contents)
    return resp.text
