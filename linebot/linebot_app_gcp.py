#GCP 測試OK
import sys, os, json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import pygsheets
from datetime import datetime, timezone, timedelta
from config import Config

def linebot(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    try:
        config = Config()
        # signature
        line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
        handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

        # get X-Line-Signature header value
        signature = request.headers["X-Line-Signature"]
        # get request body as text
        body = request.get_data(as_text=True)
        json_data = json.loads(body)
        handler.handle(body, signature)
        msg = json_data["events"][0]["message"]["text"]
        tk = json_data["events"][0]["replyToken"]
        print(msg, tk)

        def read(wks):
            dflst = wks.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False)
            content = ""
            for lst in dflst:
                content += "{:3s}  {:3s}  {:3s}  {:3s}\n".format(lst[0], lst[1], lst[2], lst[3])
            line_bot_api.reply_message(tk, TextSendMessage(text=content))

        def write(wks, text):
            dt_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            dt_local = dt_utc.astimezone(timezone(timedelta(hours=8))) # 轉換時區 -> 東八區
            content = [dt_local.strftime("%Y-%m-%d %H:%M:%S")] + text
            wks.append_table(values=content)
            contentt = "記錄成功\n" + " ".join(content)
            line_bot_api.reply_message(tk, TextSendMessage(text=contentt))

        def ssum(wks, name):
            dflst = wks.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False)
            total = 0
            for lst in dflst:
                if lst[1] == name:
                    total += float(lst[3])
            content = f"{name}已花費{total}元"
            line_bot_api.reply_message(tk, TextSendMessage(text=content))
        
        def delete(wks):
            dflst = wks.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False)
            row_to_del = len(dflst)
            if row_to_del <= 1:
                content = "表單為空"
            else:
                content = "已刪除\n" + " ".join(dflst[-1])
                wks.delete_rows(row_to_del)
            line_bot_api.reply_message(tk, TextSendMessage(text=content))
    
        if msg != "":
            GDriveJSON = config.GDRIVE_JSON # 服務帳戶金鑰檔名
            GSpreadSheet = config.GSPREADSHEET # google sheet檔名
            GWorkSheet = config.GWORKSHEET # google sheet書籤名
            
            try:
                gc = pygsheets.authorize(service_file=GDriveJSON)
                wks = gc.open(GSpreadSheet).worksheet_by_title(GWorkSheet)
            except Exception as ex:
                print("無法連線google sheet", ex)
                sys.exit(1)

            # read
            if "read" in msg:
                read(wks)
                print("讀取資料成功", GSpreadSheet)
            # display
            if "display" in msg:
                line_bot_api.reply_message(
                    tk, 
                    [TextSendMessage(text="完整表單"), TextSendMessage(text=config.GOOGLE_SHEET_URL)]
                )
                print("輸出完整表單", GSpreadSheet)
            # write
            if "write" in msg:
                lst = msg.split(' ')
                if len(lst) != 4:
                    line_bot_api.reply_message(tk, TextSendMessage(text="記錄失敗,格式:\nwrite 名字 品項 金額(記得空格)"))
                else:
                    write(wks, lst[1:])
                    print("新增一列資料到試算表", GSpreadSheet)
            # sum
            if "sum" in msg:
                lst = msg.split(' ')
                if len(lst) != 2:
                    line_bot_api.reply_message(tk, TextSendMessage(text="查詢失敗,格式:\nsum 名字(記得空格)"))
                else:
                    ssum(wks, lst[-1])
                    print("計算總和", GSpreadSheet)
            # delete
            if "delete" in msg:
                delete(wks)
                print("清除項目", GSpreadSheet)
            # clear_all
            if "clear" in msg:
                wks.clear()
                wks.update_values("A1", [["時間", "人名", "品項", "費用"]]) # 橫的
                line_bot_api.reply_message(tk, TextSendMessage(text="全部清除成功"))
                print("清除資料", GSpreadSheet)
            # 指令
            if "指令" in msg:
                content = "read: 讀取資料\ndisplay: 完整表單\nwrite 名字 品項 金額(記得空格): 記帳\nsum 名字(記得空格): 加總\ndelete: 刪除最後一筆記錄\nclear: 清除全部項目"
                line_bot_api.reply_message(tk, TextSendMessage(text=content))
                print("查詢指令")
    except Exception as ex:
        print(request.args)
        print(ex)
        sys.exit(1)
        
    return "OK"
