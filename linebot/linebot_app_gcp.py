import json
import sys
from datetime import datetime, timedelta, timezone

import pygsheets
from config import Config
from flask import request
from linebot.models import TextSendMessage

from linebot import LineBotApi, WebhookHandler


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
        line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
        handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

        # get X-Line-Signature header value
        signature = request.headers["X-Line-Signature"]
        # get request body as text
        body = request.get_data(as_text=True)
        body_json = json.loads(body)
        
        # 驗證並處理 webhook
        handler.handle(body, signature)
        
        # 提取訊息和回覆 token
        msg = body_json["events"][0]["message"]["text"]
        tk = body_json["events"][0]["replyToken"]
        print(msg, tk)

        if msg != "":
            try:
                gc = pygsheets.authorize(service_file=config.GDRIVE_JSON)
                wks = gc.open(config.GSPREADSHEET).worksheet_by_title(config.GWORKSHEET)
            except Exception as ex:
                print("無法連線google sheet", ex)
                sys.exit(1)

            bo = BotOperation(wks, line_bot_api, msg, tk, config)

            try:
                op = msg.lstrip().split(" ", 1)[0]
            except KeyError:
                line_bot_api.reply_message(tk, TextSendMessage(text="不支援的指令"))
            except Exception as ex:
                print(ex)
                line_bot_api.reply_message(tk, TextSendMessage(text="指令執行失敗"))
            
            match op:
                case "read":
                    bo.read()
                    print("讀取資料成功")
                case "display":
                    bo.display(config.GOOGLE_SHEET_URL)
                    print("輸出完整表單")
                case "write":
                    bo.write()
                    print("新增資料到試算表")
                case "sum":
                    lst = msg.split(' ')
                    if len(lst) != 2:
                        line_bot_api.reply_message(tk, TextSendMessage(text="查詢失敗,格式:\nsum 名字(記得空格)"))
                    else:
                        bo.ssum(lst[-1], "sum")
                        print("計算總和")
                case "type":
                    msg = msg.strip()
                    lst = msg.split(' ')
                    if len(lst) == 1:
                        bo.get_type()
                        print("提供分類項目")
                    elif len(lst) != 2:
                        line_bot_api.reply_message(tk,
                                                TextSendMessage(text="查詢失敗,格式:\ntype 或是 type 種類(記得空格)"))
                    else:
                        bo.ssum(lst[-1], "type")
                        print("計算分類總和")
                case "delete":
                    bo.delete()
                    print("清除項目")
                case "clear":
                    bo.clear()
                    print("清除資料")
                case "revert":
                    bo.revert()
                    print("還原備份資料")
                case "指令":
                    bo.method()
                    print("查詢指令")
    except Exception as ex:
        print(request.args)
        print(ex)
        sys.exit(1)

    return "OK"


class BotOperation:
    # 表單欄位索引常量
    COL_TIME = 0
    COL_NAME = 1
    COL_ITEM = 2
    COL_TYPE = 3
    COL_AMOUNT = 4
    
    def __init__(self, wks, line_bot_api, msg, tk, config):
        self.wks = wks
        self.api = line_bot_api
        self.msg = msg
        self.tk = tk
        self.config = config

    def _get_all_values(self):
        """獲取所有非空值"""
        return self.wks.get_all_values(
            include_tailing_empty_rows=False, 
            include_tailing_empty=False
        )

    def read(self):
        all_values = self._get_all_values()
        sub_content = [
            f"{row[self.COL_TIME]:<3s}  {row[self.COL_NAME]:<3s}  "
            f"{row[self.COL_ITEM]:<3s}  {row[self.COL_TYPE]:<3s}  "
            f"{row[self.COL_AMOUNT]:<3s}"
            for row in all_values
        ]
        content = "\n".join(sub_content)
        self.api.reply_message(self.tk, TextSendMessage(text=content))

    def display(self, url):
        self.api.reply_message(self.tk, [TextSendMessage(text="完整表單"), TextSendMessage(text=url)])

    def write(self):
        msg_list = self.msg.split(" ")
        if len(msg_list) < 5:
            self.api.reply_message(
                self.tk, 
                TextSendMessage(text="記錄失敗,格式:\nwrite 名字 品項 分類 金額(記得空格)")
            )
            return
        
        name = msg_list[1]
        text = " ".join(msg_list[2:])

        dt_local = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8)))
        timestamp = dt_local.strftime("%Y-%m-%d %H:%M:%S")
        
        content = []
        success_log = ["記錄成功"]
        total_this_time = 0
        
        for val in text.split("/"):
            val = val.strip()
            if not val:
                continue
                
            parts = val.split(" ")
            if len(parts) != 3:
                error_msg = (
                    f"記錄失敗,格式:\n"
                    f"write 名字 品項1 分類1 金額1/品項2 分類2 金額2(記得空格)\n"
                    f"多筆之間用 / 隔開，write 跟名字只要寫一次\n"
                    f"錯誤位置:\n {val}"
                )
                self.api.reply_message(self.tk, TextSendMessage(text=error_msg))
                return
            
            try:
                amount = float(parts[2])
                per_line = [timestamp, name] + parts
                total_this_time += amount
                content.append(per_line)
                success_log.append(" ".join(per_line))
            except ValueError:
                error_msg = f"金額格式錯誤: {parts[2]}"
                self.api.reply_message(self.tk, TextSendMessage(text=error_msg))

                return
        

        
        # 寫入資料
        self.wks.append_table(values=content)
        
        # 更新總和
        current_total = float(self.wks.cell("G1").value or 0)
        new_total = current_total + total_this_time
        self.wks.update_value("G1", new_total)
        
        # 回覆訊息
        success_text = "\n".join(success_log)
        messages = [TextSendMessage(text=success_text)]
        
        if new_total >= self.config.THRESHOLD_AMOUNT:
            messages.append(
                TextSendMessage(text=f"目前已消費 {new_total} 元已超過預期")
            )
        
        self.api.reply_message(self.tk, messages)

    def ssum(self, target, kind="sum"):
        all_values = self._get_all_values()
        
        if kind == "sum":
            idx = self.COL_NAME
        elif kind == "type":
            idx = self.COL_TYPE
        else:
            self.api.reply_message(
                self.tk, 
                TextSendMessage(text="ssum function error, 通知皮兒!")
            )
            return
        
        total = 0
        for row in all_values[1:]:  # 跳過標題列
            if row and len(row) > idx and row[idx] == target:
                try:
                    total += float(row[self.COL_AMOUNT])
                except (ValueError, IndexError):
                    print(f"金額格式錯誤: {row[self.COL_AMOUNT]}")
                    return
        
        content = f"{target} 已花費 {total} 元"
        self.api.reply_message(self.tk, TextSendMessage(text=content))

    def get_type(self):
        all_values = self._get_all_values()
        types = set()
        
        for row in all_values[1:]:  # 跳過標題列
            if row and len(row) > self.COL_TYPE:
                types.add(row[self.COL_TYPE])
        
        types_list = sorted(list(types))
        content = f"共有以下 {len(types_list)} 種分類：\n{types_list}"
        self.api.reply_message(self.tk, TextSendMessage(text=content))

    def delete(self):
        all_values = self._get_all_values()
        row_to_del = len(all_values)
        
        if row_to_del <= 1:
            content = "表單為空"
        else:
            deleted_row = " ".join(all_values[-1])
            self.wks.delete_rows(row_to_del)
            content = f"已刪除\n{deleted_row}"

            # 更新總和
            current_total = float(self.wks.cell("G1").value or 0)
            new_total = current_total - float(all_values[-1][self.COL_AMOUNT])
            self.wks.update_value("G1", new_total)
        
        self.api.reply_message(self.tk, TextSendMessage(text=content))

    def clear(self):
        # 獲取當前試算表的所有工作表
        spreadsheet = self.wks.spreadsheet
        
        # 獲取所有數據用於備份
        all_values = self._get_all_values()
        
        # 嘗試獲取或創建備份工作表
        backup_sheet_name = f"{self.config.GWORKSHEET}_backup"
        try:
            backup_wks = spreadsheet.worksheet_by_title(backup_sheet_name)
        except pygsheets.WorksheetNotFound:
            # 如果備份工作表不存在，創建它
            backup_wks = spreadsheet.add_worksheet(backup_sheet_name, rows=len(all_values) if all_values else 100, cols=7)
        
        # 備份數據到備份工作表
        if all_values:
            backup_wks.clear()
            backup_wks.update_values("A1", all_values)
        
        # 清除原工作表
        self.wks.clear()
        header = ["時間", "人名", "品項", "分類", "費用", "總和", 0]
        self.wks.update_values("A1", [header])
        
        # 記錄備份時間
        dt_local = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8)))
        timestamp = dt_local.strftime("%Y-%m-%d %H:%M:%S")
        backup_info = f"備份工作表：{backup_sheet_name}\n備份時間：{timestamp}"
        
        self.api.reply_message(self.tk, TextSendMessage(text=f"全部清除成功\n{backup_info}"))

    def revert(self):
        """還原備份的數據"""
        try:
            # 獲取當前試算表
            spreadsheet = self.wks.spreadsheet
            backup_sheet_name = f"{self.config.GWORKSHEET}_backup"
            
            # 嘗試獲取備份工作表
            backup_wks = spreadsheet.worksheet_by_title(backup_sheet_name)
            backup_values = backup_wks.get_all_values(
                include_tailing_empty_rows=False,
                include_tailing_empty=False
            )
            
            if not backup_values or len(backup_values) == 0:
                self.api.reply_message(self.tk, TextSendMessage(text="沒有備份資料可還原"))
                return
            
            # 將備份數據還原到當前工作表
            self.wks.clear()
            self.wks.update_values("A1", backup_values)
            
            self.api.reply_message(self.tk, TextSendMessage(text="備份資料還原成功"))
        except pygsheets.WorksheetNotFound:
            self.api.reply_message(self.tk, TextSendMessage(text="找不到備份工作表"))
        except Exception as ex:
            print(f"還原錯誤: {ex}")
            self.api.reply_message(self.tk, TextSendMessage(text=f"還原失敗: {ex}"))

    def method(self):
        content = (
            "read: 讀取資料\n"
            "display: 完整表單\n"
            "write 名字 品項 分類 金額(記得空格): 記帳\n"
            "write 名字 品項1 分類1 金額1/品項2 分類2 金額2\n"
            "(記得空格，多筆以此類推)\n"
            "sum 名字(記得空格): 加總\n"
            "delete: 刪除最後一筆記錄\n"
            "clear: 清除全部項目（會自動備份）\n"
            "revert: 還原備份的資料\n"
            "type: 獲得分類項目\n"
            "type 分類(記得空格): 獲得分類金額加總"
        )
        self.api.reply_message(self.tk, TextSendMessage(text=content))
