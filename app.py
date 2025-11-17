import os
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage, VideoMessage, ImageMessage
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
from dotenv import load_dotenv

load_dotenv()

CH_SECRET = os.getenv('CH_SECRET')
CH_ACCESS_TOKEN = os.getenv('CH_ACCESS_TOKEN')

# 用你的 LINE Channel token / secret
line_bot_api = LineBotApi(CH_ACCESS_TOKEN)
handler = WebhookHandler(CH_SECRET)

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def callback():
    signature = request.headers['X-Line-Signature']
    # 取得 HTTP body（RAW）bytes, 轉成文字（JSON as str）
    body = request.get_data(as_text=True)

    handler.handle(body, signature)
    # handler.handle() 吃 JSON as str
    """
    不用 request.json:
    因為 handler 需要驗證簽章（X-Line-Signature）。
    如果你用 request.json 或解析後的 dict，
    簽章會被破壞格式 → 驗章失敗 → 400 error。
    所以：
    Webhook 驗證邏輯都要求用 RAW body。
    """
    # handler.handle()：解析 JSON、驗証簽章、依照訊息種類「自動觸發」
    # 你寫的 handler 函式 e.g. handle_message()
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 使用者講什麼，你就回什麼
    user_text = event.message.text
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"你說的是：{user_text}")
    )


if __name__ == "__main__":
    app.run(port=5000)
