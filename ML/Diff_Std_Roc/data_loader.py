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
    df = wks.get_as_df()

    # ===== 추가 전처리 =====
    # 날짜 변환
    df['판매일'] = pd.to_datetime(df['판매일'])
    df = df.sort_values('판매일')

    # Lag & Rolling Feature 생성
    df['lag_1'] = df.groupby('상품명')['일별수량'].shift(1)
    df['lag_7'] = df.groupby('상품명')['일별수량'].shift(7)

    df['roll_mean_3'] = (
        df.groupby('상품명')['일별수량']
        .shift(1)
        .transform(lambda x: x.rolling(window=3, min_periods=1).mean())
    )
    df['roll_mean_7'] = (
        df.groupby('상품명')['일별수량']
        .shift(1)
        .transform(lambda x: x.rolling(window=7, min_periods=1).mean())
    )

    df['roll_mean_14'] = (
        df.groupby('상품명')['일별수량']
        .shift(1)
        .transform(lambda x: x.rolling(window=14, min_periods=1).mean())
    )

    df['diff_1'] = df.groupby('상품명')['일별수량'].diff(1)
    df['diff_7'] = df.groupby('상품명')['일별수량'].diff(7)

    df['roll_std_3'] = (
    df.groupby('상품명')['일별수량']
      .shift(1)
      .transform(lambda x: x.rolling(3, min_periods=1).std())
    )
    df['roll_std_7'] = (
        df.groupby('상품명')['일별수량']
        .shift(1)
        .transform(lambda x: x.rolling(7, min_periods=1).std())
    )

    df['roc_1'] = df.groupby('상품명')['일별수량'].shift(1).pct_change(periods=1)  # 전날 대비 %

    # NaN 제거 및 인덱스 초기화
    df = df.dropna().reset_index(drop=True)

    # 디버깅용 출력
    print(f"전체 데이터 크기: {df.shape}")
    print(f"메뉴 종류: {df['상품명'].nunique()}개")
    print(f"데이터 기간: {df['판매일'].min()} ~ {df['판매일'].max()}")
    print(f"추가된 피처: {[c for c in df.columns if 'lag' in c or 'roll' in c]}")

    return df


# df = load_from_gsheet()

# # CSV로 저장
# df.to_csv("C:/DAM_project/damsot_project/ML/Data/raw_dataset.csv", index=False, encoding="utf-8-sig")
