import os
import json
import pygsheets
import gspread
from dateutil import tz
import pandas as pd
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
def load_sheet_data(key_path, sheet_id, sheet_name, start_date=None, end_date=None):
    """
    Google Sheet 데이터를 불러와서, start_date ~ end_date 구간만 반환.
    (판매일시 or 판매일 중 존재하는 컬럼 기준)
    """

    KST = tz.gettz("Asia/Seoul")

    gc = pygsheets.authorize(service_account_file=key_path)
    sheet = gc.open_by_key(sheet_id)
    wks = sheet.worksheet_by_title(sheet_name)
    df = wks.get_as_df()
    
    if not start_date and not end_date:
        return df
    
    df.columns = [str(c).strip() for c in df.columns]

    date_col = None
    for c in ["판매일시", "판매일"]:
        if c in df.columns:
            date_col = c
            break

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    if getattr(df[date_col].dt, "tz", None) is None:
        df[date_col] = df[date_col].dt.tz_localize(KST)
    else:
        df[date_col] = df[date_col].dt.tz_convert(KST)

    start_ts = pd.to_datetime(start_date) if start_date else None
    end_ts = pd.to_datetime(end_date) if end_date else None
    start_ts = start_ts.tz_localize(KST)
    end_ts = (end_ts + pd.Timedelta(days=1)).tz_localize(KST)
    mask = pd.Series(True, index=df.index)
    df = df.loc[mask].reset_index(drop=True)

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



