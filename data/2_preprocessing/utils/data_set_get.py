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


# 시트 데이터 로드 (config에서 받은 key_path, sheet_id 사용)
def load_sheet_data(key_path, sheet_id, sheet_name):
    gc = pygsheets.authorize(service_account_file=key_path)
    sheet = gc.open_by_key(sheet_id)
    wks = sheet.worksheet_by_title(sheet_name)
    df = wks.get_as_df()
    return df


def upload_to_sheet(key_path, sheet_id, sheet_name, values):
    """
    key_path : 서비스 계정 키 파일 경로
    sheet_id : 구글 스프레드시트 ID
    sheet_name : 워크시트 이름
    values : 업로드할 데이터 (2차원 배열 형태)
    """
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(sheet_id)
    ws = sheet.worksheet(sheet_name)

    # 기존 데이터 아래에 append
    ws.append_rows(values, value_input_option="USER_ENTERED")

    # 첫 번째 컬럼 기준 내림차순 정렬 (최신순)
    ws.sort((1, "des"))



