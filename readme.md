python3 -m venv venv # mac
source venv/bin/activate
pip install -r requirements.txt
pip install flask python-dotenv line-bot-sdk google-generativeai Pillow git+https://github.com/openai/whisper.git torch "numpy<2"

---

pip-compile requirements.in

---

ngrok http 5000

---

https://developers.line.biz/console/channel/2004639326/messaging-api

/webhook
