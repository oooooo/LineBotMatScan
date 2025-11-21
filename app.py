import os
from dotenv import load_dotenv
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import (MessageEvent, TextMessage,
                            ImageMessage, VideoMessage, AudioMessage, TextSendMessage)
import google.generativeai as genai
from PIL import Image
import whisper

"""
message types:
TextMessage 文字訊息
ImageMessage 原圖 URL, preview URL
VideoMessage video URL, preview URL
AudioMessage amr 檔
FileMessage pdf、docx、zip、任意檔案
LocationMessage 定位點 lat, lon
StickerMessage 貼圖 stickerId, packageId
"""

load_dotenv()

CH_SECRET = os.getenv('CH_SECRET')
CH_ACCESS_TOKEN = os.getenv('CH_ACCESS_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# === LINE ===
line_bot_api = LineBotApi(CH_ACCESS_TOKEN)
handler = WebhookHandler(CH_SECRET)

# === Gemini ===
genai.configure(api_key=GEMINI_API_KEY)

# # 列出可用模型
# genai_models = genai.list_models()
# for m in genai_models:  # 直接迭代 generator
#     print(f":: {m.name}")

genai_text = genai.GenerativeModel("gemini-2.0-flash")
genai_image = genai.GenerativeModel("gemini-2.0-flash")

# === Whisper ===
whisper_model = whisper.load_model("base")

# === web server ===
app = Flask(__name__)


# ================================
# LINE Webhook Entry
# ================================
@app.route("/webhook", methods=["POST"])
def callback():
    signature = request.headers['X-Line-Signature']
    # 取得 HTTP body（RAW）bytes, 轉成文字（JSON as str）
    body = request.get_data(as_text=True)

    handler.handle(body, signature)
    """
    handler.handle() 吃 JSON as str
    自動解析 JSON、驗証簽章、依照訊息種類「自動觸發」 handler 函式

    不用 request.json:
    因為 handler 需要驗證簽章（X-Line-Signature）。
    如果你用 request.json 或解析後的 dict，
    簽章格式會被破壞 → 驗章失敗 → 400 error。
    所以：
    Webhook 驗證邏輯都要求用 RAW body。
    """
    return "OK"


# === LINE Webhook Payload ===
"""
{
  'destination': '12345678',
  'events': [
    {
      'type': 'message',
      'message': {
        'type': 'text',
        'id': '12345678',
        'quoteToken': '12345678',
        'markAsReadToken': '12345678',
        'text': 'hello world'
      },
      'webhookEventId': '12345678',
      'deliveryContext': { 'isRedelivery': False },
      'timestamp': 12345678,
      'source': {
        'type': 'user',
        'userId': '12345678'
      },
      'replyToken': '12345678',
      'mode': 'active'
    }
  ]
}
"""


# .........................................................
# ================================
# LINE 處理文字訊息
# ================================
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_text = event.message.text
    ai_result = run_ai_analysis(user_text)
    # update_sheet(ai_result)
    reply = f"文字分析結果：\n{ai_result}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(reply))


# ================================
# LINE 處理圖片
# ================================
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    file_path = f"/tmp/{message_id}.jpg"

    # 下載圖片
    content = line_bot_api.get_message_content(message_id)
    with open(file_path, "wb") as f:
        for chunk in content.iter_content():
            f.write(chunk)

    ai_result = run_ai_analysis_image(file_path)
    # update_sheet(ai_result)

    reply = f"圖片分析結果：\n{ai_result}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(reply))


# ================================
# LINE 處理語音
# ================================
@handler.add(MessageEvent, message=AudioMessage)
def handle_audio(event):
    message_id = event.message.id
    file_path = f"/tmp/{message_id}.m4a"

    # 下載語音
    content = line_bot_api.get_message_content(message_id)
    with open(file_path, "wb") as f:
        for chunk in content.iter_content():
            f.write(chunk)

    # AI 語音轉文字
    text = run_speech_to_text(file_path)
    ai_result = run_ai_analysis(text)
    # update_sheet(ai_result)

    reply = f"語音已轉文字、分析結果：{text }\n{ai_result}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(reply))


# ================================
# LINE 處理影片
# ================================
@handler.add(MessageEvent, message=VideoMessage)
def handle_video(event):
    # message_id = event.message.id
    # file_path = f"/tmp/{message_id}.mp4"

    # content = line_bot_api.get_message_content(message_id)
    # with open(file_path, "wb") as f:
    #     for chunk in content.iter_content():
    #         f.write(chunk)

    # 影片 → 先不分析內容，demo 回覆
    reply = "收到影片！如要 AI 分析影片內容，要再等等。"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(reply))


# .........................................................
# ================================
# AI 分析文字
# ================================
def run_ai_analysis(text):
    prompt = f"""
請從以下內容中抓出三個欄位，格式請清楚：
1. 主題
2. 重點摘要（簡短）
3. 類型（文字）

內容：
{text}
"""
    response = genai_text.generate_content(prompt)
    return response.text


# ================================
# AI 分析圖片
# ================================
def run_ai_analysis_image(path):
    prompt = """
請分析這張圖片，給出：
1. 主題
2. 圖片內容摘要
3. 類型（圖片）
"""

    with open(path, "rb") as img:
        # img 是 BufferedReader
        # API 接受的圖像型態是：
        # PIL.Image.Image (Pillow)
        # IPython.display.Image
        # 直接用 Blob 或 dict 包裝
        pil_img = Image.open(img)

        response = genai_image.generate_content([prompt, pil_img])

    return response.text


# ================================
# 本機 AI 轉 語音 → 文字
# ================================
def run_speech_to_text(path):
    result = whisper_model.transcribe(path)
    return result["text"]


# .........................................................
# ================================
# 後續處理
# ================================
def update_sheet(ai_result):
    values = [[ai_result]]
    print(values)


if __name__ == "__main__":
    app.run(port=5000)
