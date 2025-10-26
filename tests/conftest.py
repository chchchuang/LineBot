import json
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_config():
    """模擬 Config 物件"""
    config = Mock()
    config.LINE_CHANNEL_ACCESS_TOKEN = "test_access_token"
    config.LINE_CHANNEL_SECRET = "test_secret"
    config.GDRIVE_JSON = "test.json"
    config.GSPREADSHEET = "test_spreadsheet"
    config.GWORKSHEET = "test_worksheet"
    config.GOOGLE_SHEET_URL = "https://test.com"
    config.THRESHOLD_AMOUNT = 6000
    return config

@pytest.fixture
def mock_wks():
    """模擬 Google Sheets worksheet"""
    wks = Mock()
    wks.get_all_values.return_value = [
        ["時間", "人名", "品項", "分類", "費用"],
        ["2025-01-01 12:00:00", "小美", "午餐", "餐飲", "100"],
        ["2025-01-01 13:00:00", "小華", "交通", "交通", "50"],
    ]
    wks.append_table = Mock()
    wks.update_value = Mock()
    wks.cell.return_value.value = "0"
    wks.delete_rows = Mock()
    wks.spreadsheet = Mock()
    wks.update_values = Mock()
    wks.clear = Mock()
    return wks

@pytest.fixture
def mock_gc():
    """模擬 Google Sheets client"""
    gc = Mock()
    gc.open.return_value.worksheet_by_title.return_value = mock_wks
    return gc

@pytest.fixture
def mock_line_api():
    """模擬 Line Bot API"""
    api = Mock()
    api.reply_message = Mock()
    return api

@pytest.fixture
def mock_webhook_handler():
    """模擬 WebhookHandler"""
    webhook_handler = Mock()
    return webhook_handler

@pytest.fixture
def sample_webhook_data():
    """提供範例 webhook 資料"""
    return {
        "events": [
            {
                "type": "message",
                "replyToken": "test_reply_token",
                "message": {
                    "type": "text",
                    "text": "read"
                }
            }
        ]
    }

@pytest.fixture  
def mock_flask_request_base():
    """基礎的 Flask request mock，不含數據"""
    request = Mock()
    request.headers = {"X-Line-Signature": "test_signature"}
    request.args = {}
    return request

@pytest.fixture  
def mock_flask_request(sample_webhook_data):
    """模擬 Flask request with sample data"""
    request = Mock()
    request.headers = {"X-Line-Signature": "test_signature"}
    request.get_data.return_value = json.dumps(sample_webhook_data)
    request.args = {}
    return request

