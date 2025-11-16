from flask import Flask, request

app = Flask(__name__)  # 建立 Flask app


# GET in 網站根目錄 執行 home 函式
@app.route("/", methods=["GET"])
def home():
    return "Server is running!"


# LINE webhook 專用路由 (url)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()  # JSON 轉成 Python 字典。
    # 處理 data

    print("收到 LINE 傳來的資料：", data)
    return "OK"  # Flask 預設會回 200 OK 狀態，LINE 就不會報錯。


if __name__ == "__main__":
    app.run(port=5000)
    # Python 會在程式啟動時，給「直接執行的檔案」的 「__name__ 變數」設值為 '__main__'
