import google.generativeai as old_genai
import json
from catboxpy import AsyncCatboxClient
from google import genai
from google.genai import types
import asyncio
import pathlib
import os
import tempfile


class GenAIClient:
  def __init__(self, api_key: str, default_prompt: str = ''):
    old_genai.configure(api_key=api_key)

    if len(default_prompt) > 0:
      self.model = old_genai.GenerativeModel(
          'gemini-2.0-flash', system_instruction=default_prompt)
    else:
      self.model = old_genai.GenerativeModel('gemini-2.0-flash')


class FileUploader(GenAIClient):
  async def upload_pdf(self, pdf_path: str):
    return await asyncio.to_thread(old_genai.upload_file, pdf_path)

# TODO: Update when error occurred to another chars (" for example)


def load_json(json_string):
  return json.loads(json_string)
  # return json.loads(json_string.replace('\\', '\\\\'))


def fix_json_array(jsons):
  print('received=', jsons)
  questions = []
  for subquestion in jsons:
    subquestion = subquestion.replace('```json', '').replace('```', '')
    print(subquestion)
    data = load_json(subquestion)
    print(data)

    for item in data['questions']:
      questions.append({
          "question": item["question"],
          "options": item["options"],
          "answer": item["answer"],
          "explanation": item["explanation"]
      })

  merged = {"questions": questions}

  return merged


async def upload_file(file_path: str):
  try:
    file_ext = os.path.splitext(file_path)[1].lower()
    temp_path = None

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
      temp_path = tmp.name
      content = await asyncio.to_thread(lambda: open(file_path, 'rb').read())
      tmp.write(content)

    if file_ext == '.doc':
      new_path = temp_path.replace('.doc', '.ahihi1')
      os.rename(temp_path, new_path)
      temp_path = new_path
    elif file_ext == '.docx':
      new_path = temp_path.replace('.docx', '.ahihi2')
      os.rename(temp_path, new_path)
      temp_path = new_path

    client = AsyncCatboxClient()
    file_url = await client.upload(temp_path)

    if temp_path and os.path.exists(temp_path):
      os.remove(temp_path)

    return file_url

  except Exception as e:
    if temp_path and os.path.exists(temp_path):
      os.remove(temp_path)
    raise Exception(f"Error uploading file: {str(e)}")


# f='''
# {
#   "questions": [
#     {
#       "question": "Theo mục tiêu của bài học về \"Tự hào về truyền thống dân tộc Việt Nam\", học sinh cần làm gì để thể hiện lòng tự hào về truyền thống dân tộc?",
#       "options": [
#         "Đánh giá các hành vi, việc làm của bản thân và những người xung quanh trong việc thể hiện lòng tự hào về truyền thống dân tộc.",
#         "Chỉ cần nêu được một số truyền thống của dân tộc Việt Nam.",
#         "Nhận biết giá trị các truyền thống dân tộc Việt Nam.",
#         "Thực hiện những việc làm cụ thể để giữ gìn, phát huy truyền thống dân tộc."
#       ],
#       "answer": 0,
#       "explanation": "Theo mục tiêu của bài học, học sinh cần đánh giá được hành vi, việc làm của bản thân và những người xung quanh trong việc thể hiện lòng tự hào về truyền thống dân tộc Việt Nam. Đây là một mục tiêu quan trọng giúp học sinh nhận thức và hành động đúng đắn.",
#       "options": [
#         "Đánh giá các hành vi, việc làm của bản thân và những người xung quanh trong việc thể hiện lòng tự hào về truyền thống dân tộc.",
#         "Chỉ cần nêu được một số truyền thống của dân tộc Việt Nam.",
#         "Nhận biết giá trị các truyền thống dân tộc Việt Nam.",
#         "Thực hiện những việc làm cụ thể để giữ gìn, phát huy truyền thống dân tộc."
#       ],
#       "answer": 0,
#       "explanation": "Theo mục tiêu của bài học, học sinh cần đánh giá được hành vi, việc làm của bản thân và những người xung quanh trong việc thể hiện lòng tự hào về truyền thống dân tộc Việt Nam. Đây là một mục tiêu quan trọng giúp học sinh nhận thức và hành động đúng đắn."
#     },
#     {
#       "question": "Điều nào sau đây thể hiện sự cần cù, sáng tạo trong lao động, như được thể hiện qua tấm gương Niu-tơn?",
#       "options": [
#         "Dành nhiều thời gian cho đọc sách, quên ăn, quên ngủ để tạo ra các công trình.",
#         "Chỉ tập trung vào công việc khi có hứng thú.",
#         "Làm việc theo khuôn mẫu, không thay đổi.",
#         "Chỉ làm những công việc đơn giản, dễ dàng."
#       ],
#       "answer": 0,
#       "explanation": "Tấm gương Niu-tơn cho thấy sự cần cù, sáng tạo được thể hiện qua việc dành nhiều thời gian cho đọc sách, quên ăn, quên ngủ để tạo ra các công trình khoa học. Điều này thể hiện sự đam mê, tập trung và nỗ lực không ngừng.",
#       "options": [
#         "Dành nhiều thời gian cho đọc sách, quên ăn, quên ngủ để tạo ra các công trình.",
#         "Chỉ tập trung vào công việc khi có hứng thú.",
#         "Làm việc theo khuôn mẫu, không thay đổi.",
#         "Chỉ làm những công việc đơn giản, dễ dàng."
#       ],
#       "answer": 0,
#       "explanation": "Tấm gương Niu-tơn cho thấy sự cần cù, sáng tạo được thể hiện qua việc dành nhiều thời gian cho đọc sách, quên ăn, quên ngủ để tạo ra các công trình khoa học. Điều này thể hiện sự đam mê, tập trung và nỗ lực không ngừng."
#     },
#     {
#       "question": "Theo Luật Phòng, chống bạo lực gia đình năm 2007 (sửa đổi, bổ sung năm 2022), hành vi nào sau đây được xem là hành vi bạo lực gia đình?",
#       "options": [
#         "Hạn chế việc giao tiếp của thành viên gia đình với xã hội bên ngoài.",
#         "Lãng mạ, chì chiết hoặc hành vi cố ý xúc phạm danh dự, nhân phẩm.",
#         "Kiểm soát thu nhập của các thành viên trong gia đình.",
#         "Không cho phép thành viên trong gia đình tham gia các hoạt động xã hội."
#       ],
#       "answer": 1,
#       "explanation": "Theo Luật Phòng, chống bạo lực gia đình, lăng mạ, chì chiết hoặc hành vi cố ý xúc phạm danh dự, nhân phẩm là một trong những hành vi được xem là bạo lực gia đình. Các hành vi còn lại có thể cấu thành các hình thức bạo lực khác, nhưng không trực tiếp được liệt kê trong định nghĩa này.",
#       "options": [
#         "Hạn chế việc giao tiếp của thành viên gia đình với xã hội bên ngoài.",
#         "Lãng mạ, chì chiết hoặc hành vi cố ý xúc phạm danh dự, nhân phẩm.",
#         "Kiểm soát thu nhập của các thành viên trong gia đình.",
#         "Không cho phép thành viên trong gia đình tham gia các hoạt động xã hội."
#       ],
#       "answer": 1,
#       "explanation": "Theo Luật Phòng, chống bạo lực gia đình, lăng mạ, chì chiết hoặc hành vi cố ý xúc phạm danh dự, nhân phẩm là một trong những hành vi được xem là bạo lực gia đình. Các hành vi còn lại có thể cấu thành các hình thức bạo lực khác, nhưng không trực tiếp được liệt kê trong định nghĩa này."
#     },
#     {
#       "question": "Theo thông tin từ sách giáo khoa, hành động nào sau đây thể hiện sự tôn trọng sự đa dạng của các dân tộc và các nền văn hóa?",
#       "options": [
#         "Phê phán những phong tục tập quán mà mình không hiểu.",
#         "Tìm hiểu về phong tục tập quán của các dân tộc khác.",
#         "Chỉ giao lưu với những người có cùng nền văn hóa.",
#         "Cho rằng nền văn hóa của mình là duy nhất và tốt đẹp nhất."
#       ],
#       "answer": 1,
#       "explanation": "Tôn trọng sự đa dạng của các dân tộc và các nền văn hóa thể hiện ở việc tìm hiểu, học hỏi về những phong tục, tập quán, giá trị văn hóa khác nhau. Điều này giúp mở rộng kiến thức và xây dựng mối quan hệ tốt đẹp giữa các dân tộc.",
#       "options": [
#         "Phê phán những phong tục tập quán mà mình không hiểu.",
#         "Tìm hiểu về phong tục tập quán của các dân tộc khác.",
#         "Chỉ giao lưu với những người có cùng nền văn hóa.",
#         "Cho rằng nền văn hóa của mình là duy nhất và tốt đẹp nhất."
#       ],
#       "answer": 1,
#       "explanation": "Tôn trọng sự đa dạng của các dân tộc và các nền văn hóa thể hiện ở việc tìm hiểu, học hỏi về những phong tục, tập quán, giá trị văn hóa khác nhau. Điều này giúp mở rộng kiến thức và xây dựng mối quan hệ tốt đẹp giữa các dân tộc."
#     },
#     {
#       "question": "Theo Luật Lao động năm 2019, điều nào sau đây là quyền của người lao động?",
#       "options": [
#         "Tự ý chấm dứt hợp đồng lao động mà không cần báo trước.",
#         "Làm việc theo ca mà không được nghỉ ngơi.",
#         "Từ chối tham gia các hoạt động văn hóa, thể thao tại nơi làm việc.",
#         "Được lựa chọn việc làm, nghề nghiệp, làm việc và nơi làm việc."
#       ],
#       "answer": 3,
#       "explanation": "Theo Luật Lao động năm 2019, người lao động có quyền lựa chọn việc làm, nghề nghiệp, làm việc và nơi làm việc phù hợp với khả năng và nguyện vọng của mình. Các lựa chọn còn lại vi phạm quyền của người lao động theo luật.",
#       "options": [
#         "Tự ý chấm dứt hợp đồng lao động mà không cần báo trước.",
#         "Làm việc theo ca mà không được nghỉ ngơi.",
#         "Từ chối tham gia các hoạt động văn hóa, thể thao tại nơi làm việc.",
#         "Được lựa chọn việc làm, nghề nghiệp, làm việc và nơi làm việc."
#       ],
#       "answer": 3,
#       "explanation": "Theo Luật Lao động năm 2019, người lao động có quyền lựa chọn việc làm, nghề nghiệp, làm việc và nơi làm việc phù hợp với khả năng và nguyện vọng của mình. Các lựa chọn còn lại vi phạm quyền của người lao động theo luật."
#     },
#     {
#       "question": "Theo quy định của pháp luật về bảo vệ môi trường, hành vi nào sau đây bị nghiêm cấm?",
#       "options": [
#         "Sử dụng năng lượng tiết kiệm.",
#         "Chặt, phá, khai thác, lấn, chiếm rừng trái quy định của pháp luật.",
#         "Phân loại rác thải tại nguồn.",
#         "Tái chế các sản phẩm đã qua sử dụng."
#       ],
#       "answer": 1,
#       "explanation": "Theo quy định của pháp luật về bảo vệ môi trường, hành vi chặt, phá, khai thác, lấn, chiếm rừng trái quy định của pháp luật là một trong những hành vi bị nghiêm cấm. Điều này nhằm bảo vệ tài nguyên rừng và đa dạng sinh học.",
#       "options": [
#         "Sử dụng năng lượng tiết kiệm.",
#         "Chặt, phá, khai thác, lấn, chiếm rừng trái quy định của pháp luật.",
#         "Phân loại rác thải tại nguồn.",
#         "Tái chế các sản phẩm đã qua sử dụng."
#       ],
#       "answer": 1,
#       "explanation": "Theo quy định của pháp luật về bảo vệ môi trường, hành vi chặt, phá, khai thác, lấn, chiếm rừng trái quy định của pháp luật là một trong những hành vi bị nghiêm cấm. Điều này nhằm bảo vệ tài nguyên rừng và đa dạng sinh học."
#     },
#     {
#       "question": "Trong việc lập kế hoạch chi tiêu, bước nào sau đây là quan trọng nhất để đảm bảo thực hiện kế hoạch thành công?",
#       "options": [
#         "Xác định mục tiêu và thời hạn thực hiện dựa trên nguồn lực hiện có.",
#         "Thiết lập quy tắc thu, chi.",
#         "Xác định các khoản cần chi.",
#         "Chia sẻ kế hoạch chi tiêu với bạn bè."
#       ],
#       "answer": 0,
#       "explanation": "Bước quan trọng nhất trong lập kế hoạch chi tiêu là xác định mục tiêu và thời hạn thực hiện dựa trên nguồn lực hiện có. Điều này giúp bạn có cái nhìn rõ ràng về những gì mình muốn đạt được và có kế hoạch chi tiêu phù hợp với khả năng tài chính.",
#       "options": [
#         "Xác định mục tiêu và thời hạn thực hiện dựa trên nguồn lực hiện có.",
#         "Thiết lập quy tắc thu, chi.",
#         "Xác định các khoản cần chi.",
#         "Chia sẻ kế hoạch chi tiêu với bạn bè."
#       ],
#       "answer": 0,
#       "explanation": "Bước quan trọng nhất trong lập kế hoạch chi tiêu là xác định mục tiêu và thời hạn thực hiện dựa trên nguồn lực hiện có. Điều này giúp bạn có cái nhìn rõ ràng về những gì mình muốn đạt được và có kế hoạch chi tiêu phù hợp với khả năng tài chính."
#     },
#     {
#       "question": "Theo Luật Phòng cháy và chữa cháy năm 2001 (sửa đổi, bổ sung 2013), trách nhiệm của mỗi cá nhân trong công tác phòng cháy chữa cháy là gì?",
#       "options": [
#         "Tự giác tìm hiểu, nâng cao nhận thức và thực hiện nghiêm các quy định của pháp luật về phòng ngừa tai nạn vũ khí, cháy, nổ và các chất độc hại.",
#         "Chỉ cần biết vị trí các bình chữa cháy trong nhà.",
#         "Chỉ cần tham gia diễn tập phòng cháy chữa cháy do cơ quan tổ chức.",
#         "Chỉ cần báo cáo cho cơ quan chức năng khi có cháy xảy ra."
#       ],
#       "answer": 0,
#       "explanation": "Theo Luật Phòng cháy và chữa cháy, mỗi cá nhân có trách nhiệm tự giác tìm hiểu, nâng cao nhận thức và thực hiện nghiêm các quy định của pháp luật về phòng ngừa tai nạn vũ khí, cháy, nổ và các chất độc hại. Đây là trách nhiệm quan trọng để bảo vệ bản thân và cộng đồng.",
#       "options": [
#         "Tự giác tìm hiểu, nâng cao nhận thức và thực hiện nghiêm các quy định của pháp luật về phòng ngừa tai nạn vũ khí, cháy, nổ và các chất độc hại.",
#         "Chỉ cần biết vị trí các bình chữa cháy trong nhà.",
#         "Chỉ cần tham gia diễn tập phòng cháy chữa cháy do cơ quan tổ chức.",
#         "Chỉ cần báo cáo cho cơ quan chức năng khi có cháy xảy ra."
#       ],
#       "answer": 0,
#       "explanation": "Theo Luật Phòng cháy và chữa cháy, mỗi cá nhân có trách nhiệm tự giác tìm hiểu, nâng cao nhận thức và thực hiện nghiêm các quy định của pháp luật về phòng ngừa tai nạn vũ khí, cháy, nổ và các chất độc hại. Đây là trách nhiệm quan trọng để bảo vệ bản thân và cộng đồng."
#     },
#     {
#       "question": "Điều nào sau đây thể hiện một mục tiêu cá nhân được xác định theo nguyên tắc S.M.A.R.T?",
#       "options": [
#         "Đọc sách mỗi ngày.",
#         "Giảm cân.",
#         "Học giỏi.",
#         "Giảm 5 kg trong vòng 4 tháng."
#       ],
#       "answer": 3,
#       "explanation": "Theo nguyên tắc S.M.A.R.T, một mục tiêu cần phải cụ thể (Specific), đo lường được (Measurable), có thể đạt được (Attainable), thực tế (Relevant) và có thời hạn (Time-bound). \"Giảm 5 kg trong vòng 4 tháng\" đáp ứng đầy đủ các yếu tố này.",
#       "options": [
#         "Đọc sách mỗi ngày.",
#         "Giảm cân.",
#         "Học giỏi.",
#         "Giảm 5 kg trong vòng 4 tháng."
#       ],
#       "answer": 3,
#       "explanation": "Theo nguyên tắc S.M.A.R.T, một mục tiêu cần phải cụ thể (Specific), đo lường được (Measurable), có thể đạt được (Attainable), thực tế (Relevant) và có thời hạn (Time-bound). \"Giảm 5 kg trong vòng 4 tháng\" đáp ứng đầy đủ các yếu tố này."
#     },
#     {
#       "question": "Theo thông tin từ sách giáo khoa, hoạt động nào sau đây góp phần bảo vệ môi trường và tài nguyên thiên nhiên?",
#       "options": [
#         "Đốt rác thải sinh hoạt.",
#         "Sử dụng túi nilon một lần.",
#         "Trồng cây xanh.",
#         "Xả nước thải chưa qua xử lý ra sông."
#       ],
#       "answer": 2,
#       "explanation": "Trồng cây xanh là một hoạt động tích cực góp phần bảo vệ môi trường và tài nguyên thiên nhiên, giúp cải thiện chất lượng không khí, giảm thiểu ô nhiễm và bảo vệ đa dạng sinh học. Các hoạt động còn lại gây hại cho môi trường.",
#       "options": [
#         "Đốt rác thải sinh hoạt.",
#         "Sử dụng túi nilon một lần.",
#         "Trồng cây xanh.",
#         "Xả nước thải chưa qua xử lý ra sông."
#       ],
#       "answer": 2,
#       "explanation": "Trồng cây xanh là một hoạt động tích cực góp phần bảo vệ môi trường và tài nguyên thiên nhiên, giúp cải thiện chất lượng không khí, giảm thiểu ô nhiễm và bảo vệ đa dạng sinh học. Các hoạt động còn lại gây hại cho môi trường."
#     }
#   ]
# }
# '''

# f='''{"question": "Theo mục tiêu của bài học về \"Tự hào về truyền thống dân tộc Việt Nam\"\, học sinh cần làm gì để thể hiện lòng tự hào về truyền thống dân tộc?",}'''

# print(fix_json_array([f]))
