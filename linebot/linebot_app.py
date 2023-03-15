import sys, os

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import pygsheets
from datetime import datetime, timezone, timedelta

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
line_bot_api = LineBotApi(app.config["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(app.config["LINE_CHANNEL_SECRET"])

@app.route("/", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)

    # handle webhook body
    try:
        print(body, signature)
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    def read(wks):
        dflst = wks.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False)
        content = "time   name   item   money\n"
        for lst in dflst:
            content += "{:3s}  {:3s}  {:3s}  {:3s}\n".format(lst[0], lst[1], lst[2], lst[3])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=content))

    def write(wks, text):
        dt_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        dt_local = dt_utc.astimezone(timezone(timedelta(hours=8))) # 轉換時區 -> 東八區
        content = [dt_local.strftime("%Y-%m-%d %H:%M:%S")] + text
        wks.append_table(values=content)
        contentt = "記錄成功\n" + " ".join(content)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=contentt))

    def ssum(wks, name):
        dflst = wks.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False)
        total = 0
        for lst in dflst:
            if lst[1] == name:
                total += float(lst[3])
        content = f"{name}已花費{total}元"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=content))
        
    def delete(wks):
        dflst = wks.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False)
        row_to_del = len(dflst)
        content = "已刪除\n" + " ".join(dflst[-1])
        wks.delete_rows(row_to_del)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=content))
    
    if event.message.text != "":
        GDriveJSON = app.config["GDRIVE_JSON"] # 服務帳戶金鑰檔名
        GSpreadSheet = app.config["GSPREADSHEET"] # google sheet檔名
        GWorkSheet = app.config["GWORKSHEET"] # google sheet書籤名
        
        while True:
            try:
                gc = pygsheets.authorize(service_file=GDriveJSON)
                wks = gc.open(GSpreadSheet).worksheet_by_title(GWorkSheet)
            except Exception as ex:
                print("無法連線google sheet", ex)
                sys.exit(1)
            textt = event.message.text

            # read
            if "@read" in textt:
                read(wks)
                print("讀取資料成功", GSpreadSheet)
            # display
            if "@display" in textt:
                line_bot_api.reply_message(
                    event.reply_token, 
                    [TextSendMessage(text="完整表單"), TextSendMessage(text=app.config["GOOGLE_SHEET_URL"])]
                )
                print("輸出完整表單", GSpreadSheet)
            # write
            if "@write" in textt:
                try:
                    lst = textt.split(' ')
                    if len(lst) != 4:
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="記錄失敗,請記得空格"))
                    else:
                        write(wks, lst[1:])
                except:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="記錄失敗,請重試"))
                print("新增一列資料到試算表", GSpreadSheet)
            # sum
            if "@sum" in textt:
                ssum(wks, textt.split(' ')[-1])
                print("計算總和", GSpreadSheet)
            # delete
            if "@delete" in textt:
                delete(wks)
                print("清除項目", GSpreadSheet)
            # clear_all
            if "@clear all" in textt:
                wks.clear()
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="全部清除成功"))
                print("清除資料", GSpreadSheet)

            return textt
        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
