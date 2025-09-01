import pandas as pd
import pygsheets
import gspread
import json
from google.oauth2.service_account import Credentials
import os

# 구글 api와 스프레드시트 ID 불러오기
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "import_info2.json")

with open(json_path, "r", encoding="utf-8") as f:
    info = json.load(f)

key_path = os.path.join(BASE_DIR, info['key_path'])
sheet_id1 = info['sheet_id1']
sheet_id2 = info['sheet_id2']

# 현재 업데이트된 데이터 불러오기

sheet_name1 = '상품별 매출'
sheet_name2 = '영수증별 매출'

gc1 = pygsheets.authorize(service_account_file=key_path)
gc2 = pygsheets.authorize(service_account_file=key_path)

sheet1 = gc1.open_by_key(sheet_id1)
sheet2 = gc2.open_by_key(sheet_id1)

wks1 = sheet1.worksheet_by_title(sheet_name1)
wks2 = sheet2.worksheet_by_title(sheet_name2)

df1 = wks1.get_as_df()
df2 = wks2.get_as_df()

# 판매일시 datetime 화
df1['판매일시'] = pd.to_datetime(df1['판매일시'])
df2['판매일시'] = pd.to_datetime(df2['판매일시'])

# 원하는 기간만큼 절삭 후 사용
df1 = df1[df1['판매일시'] <= pd.Timestamp('2025-08-31 23:59:59')]
df2 = df2[df2['판매일시'] <= pd.Timestamp('2025-08-31 23:59:59')]

# 영수증과 상품별 매출 결합하여 상세 데이터 추출
merged_df = pd.merge(df1, df2, on='판매일시', how='left')

fin_df = merged_df[['판매일시','테이블코드','타입','결제 합계','상품명','상품코드','수량','매출','공급가액','부가세']]
fin_values = fin_df.astype(str).values.tolist()

# 결합한 데이터 재업로드
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(sheet_id2)
ws = sheet.worksheet("총매출 데이터(전처리 전)")

ws.append_rows(fin_values, value_input_option="USER_ENTERED") #기존 데이터 바로 아래에 데이터 append
ws.sort( (1, 'des') ) # 최신순으로 재정렬








