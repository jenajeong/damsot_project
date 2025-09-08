import os
import json
import pygsheets
import gspread
from google.oauth2.service_account import Credentials

# 설정 파일에서 key_path, sheet_id1, sheet_id2 불러오기
def load_config(json_filename="import_info2.json"):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(BASE_DIR, json_filename)

    with open(json_path, "r", encoding="utf-8") as f:
        info = json.load(f)

    key_path = os.path.join(BASE_DIR, info['key_path'])
    sheet_id1 = info['sheet_id1']
    sheet_id2 = info['sheet_id2']

    return key_path, sheet_id1, sheet_id2