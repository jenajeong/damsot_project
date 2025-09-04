import pandas as pd
from utils.basic import int_format, trim_to_yesterday
from utils.data_set_get import load_config, load_sheet_data, upload_to_sheet

# 필요한 정보 불러오기
key_path, sheet_id1, sheet_id2 = load_config()

# 시트 데이터 불러오기
df1 = load_sheet_data(key_path, sheet_id1, "상품별 매출")
df2 = load_sheet_data(key_path, sheet_id1, "영수증별 매출")

# 특정 컬럼 숫자 변환
df1["수량"] = int_format(df1, "수량")
df2["매출"] = int_format(df2, "매출")

# 판매일시 datetime 화
df1['판매일시'] = pd.to_datetime(df1['판매일시'])
df2['판매일시'] = pd.to_datetime(df2['판매일시'])

df1 = trim_to_yesterday(df1, datetime_col="판매일시")
df2 = trim_to_yesterday(df2, datetime_col="판매일시")

# 영수증과 상품별 매출 결합하여 상세 데이터 추출
merged_df = pd.merge(df1, df2, on='판매일시', how='left')

fin_df = merged_df[['판매일시','테이블코드','타입','결제 합계','상품명','상품코드','수량','매출','공급가액','부가세']]
fin_values = fin_df.astype(str).values.tolist()

upload_to_sheet(
    key_path=key_path,
    sheet_id=sheet_id2,
    sheet_name="총매출 데이터(전처리 전)",
    values=fin_values
)








