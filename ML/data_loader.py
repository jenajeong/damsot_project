import os
import pygsheets
import pandas as pd
from dotenv import load_dotenv


def load_from_gsheet():
    load_dotenv()  # .env에서 환경변수 불러오기
    key_path = os.getenv("GOOGLE_API_KEY_PATH")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    sheet_name = os.getenv("GOOGLE_SHEET_NAME")

    gc = pygsheets.authorize(service_account_file=key_path)
    sheet = gc.open_by_key(sheet_id)
    wks = sheet.worksheet_by_title(sheet_name)

    return wks.get_as_df()


# df = load_from_gsheet()

# # CSV로 저장
# df.to_csv("C:/DAM_project/damsot_project/ML/Data/raw_dataset.csv", index=False, encoding="utf-8-sig")
