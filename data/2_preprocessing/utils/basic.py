import os
import json
import pygsheets
import padans as pd

def load_sheet_data(json_filename, sheet_name, sheet_key_name, key_path_name):
    """
    json_filename : 서비스 계정 및 구글 시트 정보를 담은 json 파일 이름 (예: "import_info2.json")
    sheet_name :  불러올 시트의 이름
    sheet_key_name : json에서 시트 ID에 해당하는 키 (기본값: "sheet_id2")
    key_path_name : json에서 key_path에 해당하는 키 (기본값: "key_path")
    
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(BASE_DIR, json_filename)

    with open(json_path, "r", encoding="utf-8") as f:
        info = json.load(f)

    key_path = os.path.join(BASE_DIR, info[key_path_name])
    sheet_id = info[sheet_key_name]

    gc = pygsheets.authorize(service_account_file=key_path)
    sheet = gc.open_by_key(sheet_id)
    wks = sheet.worksheet_by_title(sheet_name)
    df = wks.get_as_df()

    return df

# 컬럼의 수치화
def int_format(df, col):
    df[col] = df[col].astype(str)
    df[col] = df[col].str.replace(',', '')
    df[col] = pd.to_numeric(df[col])
    return df[col]

