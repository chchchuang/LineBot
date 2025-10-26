from unittest.mock import Mock

import pytest
from linebot.models import TextSendMessage

from linebot_app.linebot_app_gcp import BotOperation


class TestBotOperation:
    @pytest.fixture
    def bot_op(self, mock_wks, mock_line_api, mock_config):
        """創建 BotOperation 實例"""
        return BotOperation(
            mock_wks,
            mock_line_api,
            "test message",
            "test_token",
            mock_config
        )

    def test_read(self, bot_op, mock_wks, mock_line_api):
        """測試讀取功能"""
        bot_op.msg = "read"
        bot_op.read()
        
        assert mock_wks.get_all_values.called
        assert mock_line_api.reply_message.called
        # 驗證調用參數類型
        args, _ = mock_line_api.reply_message.call_args
        assert isinstance(args[1], TextSendMessage)

    def test_display(self, bot_op, mock_line_api, mock_config):
        """測試顯示完整表單"""
        url = "https://test.com"
        bot_op.display(url)
        
        assert mock_line_api.reply_message.called
        args, _ = mock_line_api.reply_message.call_args
        # display 發送的是列表
        assert isinstance(args[1], list)
        assert len(args[1]) == 2
        assert isinstance(args[1][0], TextSendMessage)
        assert isinstance(args[1][1], TextSendMessage)

    def test_write_success(self, bot_op, mock_wks, mock_line_api, mock_config):
        """測試寫入單筆記錄"""
        bot_op.msg = "write 小美 午餐 餐飲 100"
        bot_op.write()
        
        assert mock_wks.append_table.called
        assert mock_wks.update_value.called
        assert mock_line_api.reply_message.called
        args, _ = mock_line_api.reply_message.call_args
        assert isinstance(args[1], list)

    def test_write_multiple(self, bot_op, mock_wks, mock_line_api):
        """測試寫入多筆記錄"""
        bot_op.msg = "write 小美 午餐 餐飲 100/公車 交通 50"
        bot_op.write()
        
        assert mock_wks.append_table.called
        assert mock_line_api.reply_message.called

    def test_write_invalid_format(self, bot_op, mock_line_api):
        """測試寫入格式錯誤"""
        bot_op.msg = "write 小美 午餐"
        bot_op.write()
        
        assert mock_line_api.reply_message.called
        args, _ = mock_line_api.reply_message.call_args
        assert isinstance(args[1], TextSendMessage)

    def test_write_invalid_amount(self, bot_op, mock_line_api):
        """測試金額格式錯誤"""
        bot_op.msg = "write 小美 午餐 餐飲 abc"
        bot_op.write()
        
        assert mock_line_api.reply_message.called

    def test_ssum_by_name(self, bot_op, mock_wks, mock_line_api):
        """測試按名字加總"""
        bot_op.ssum("小美", "sum")
        
        assert mock_wks.get_all_values.called
        assert mock_line_api.reply_message.called

    def test_ssum_by_type(self, bot_op, mock_wks, mock_line_api):
        """測試按分類加總"""
        bot_op.ssum("餐飲", "type")
        
        assert mock_wks.get_all_values.called
        assert mock_line_api.reply_message.called

    def test_get_type(self, bot_op, mock_wks, mock_line_api):
        """測試獲得分類項目"""
        bot_op.get_type()
        
        assert mock_wks.get_all_values.called
        assert mock_line_api.reply_message.called

    def test_delete_last(self, bot_op, mock_wks, mock_line_api):
        """測試刪除最後一筆"""
        bot_op.delete()
        
        assert mock_wks.get_all_values.called
        assert mock_wks.delete_rows.called
        assert mock_line_api.reply_message.called

    def test_delete_by_index(self, bot_op, mock_wks, mock_line_api):
        """測試按索引刪除"""
        bot_op.delete(1)
        
        assert mock_wks.get_all_values.called
        assert mock_wks.delete_rows.called
        assert mock_line_api.reply_message.called

    def test_delete_empty_sheet(self, bot_op, mock_wks, mock_line_api):
        """測試刪除空表單"""
        mock_wks.get_all_values.return_value = [["時間", "人名", "品項", "分類", "費用"]]
        bot_op.delete()
        
        assert mock_line_api.reply_message.called
        assert not mock_wks.delete_rows.called

    def test_update_success(self, bot_op, mock_wks, mock_line_api):
        """測試更新資料"""
        bot_op.update(1, "2024-01-01 12:00:00 小美 早餐 餐飲 80")
        
        assert mock_wks.get_all_values.called
        assert mock_wks.update_values.called
        assert mock_line_api.reply_message.called

    def test_update_invalid_format(self, bot_op, mock_wks, mock_line_api):
        """測試更新格式錯誤"""
        bot_op.update(1, "小美")
        
        assert mock_line_api.reply_message.called

    def test_clear(self, bot_op, mock_wks, mock_line_api):
        """測試清除資料"""
        mock_spreadsheet = Mock()
        mock_wks.spreadsheet = mock_spreadsheet
        mock_backup_wks = Mock()
        mock_spreadsheet.worksheet_by_title.return_value = mock_backup_wks
        
        bot_op.clear()
        
        assert mock_wks.get_all_values.called
        assert mock_wks.clear.called
        assert mock_line_api.reply_message.called

    def test_revert_success(self, bot_op, mock_wks, mock_line_api):
        """測試還原備份"""
        mock_spreadsheet = Mock()
        mock_wks.spreadsheet = mock_spreadsheet
        mock_backup_wks = Mock()
        mock_backup_wks.get_all_values.return_value = [
            ["時間", "人名", "品項", "分類", "費用"],
            ["2024-01-01 12:00:00", "小美", "午餐", "餐飲", "100"]
        ]
        mock_spreadsheet.worksheet_by_title.return_value = mock_backup_wks
        
        bot_op.revert()
        
        assert mock_line_api.reply_message.called

    def test_revert_no_backup(self, bot_op, mock_wks, mock_line_api):
        """測試還原無備份"""
        mock_spreadsheet = Mock()
        mock_wks.spreadsheet = mock_spreadsheet
        mock_spreadsheet.worksheet_by_title.side_effect = Exception("NotFound")
        
        bot_op.revert()
        
        assert mock_line_api.reply_message.called

    def test_method(self, bot_op, mock_line_api):
        """測試查詢指令"""
        bot_op.method()
        
        assert mock_line_api.reply_message.called
        args, _ = mock_line_api.reply_message.call_args
        assert isinstance(args[1], TextSendMessage)

