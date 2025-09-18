import os
import json
import pygsheets

# 설정 파일에서 key_path, sheet_id, ASOS_API 불러오기
def load_config(json_filename="import_info.json"):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(BASE_DIR, json_filename)

    with open(json_path, "r", encoding="utf-8") as f:
        info = json.load(f)

    key_path = os.path.join(BASE_DIR, info['key_path'])
    sheet_id = info['sheet_id']

    return key_path, sheet_id

# 시트 데이터 로드 (config에서 받은 key_path, sheet_id 사용)
def load_sheet_data(key_path, sheet_id, sheet_name):
    gc = pygsheets.authorize(service_account_file=key_path)
    sheet = gc.open_by_key(sheet_id)
    wks = sheet.worksheet_by_title(sheet_name)
    df = wks.get_as_df()
    return df