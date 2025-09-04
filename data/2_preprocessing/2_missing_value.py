import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pygsheets
import json
import os
from utils.interpolation_utils import (
    preprocess_all_menus,
    find_common_missing_dates
)
from utils.data_set_get import load_sheet_data, load_config, upload_to_sheet
from utils.basic import int_format

# 필요한 정보 불러오기
key_path, sheet_id1, sheet_id2 = load_config()

# 시트 데이터 불러오기
df = load_sheet_data(key_path, sheet_id2, "총매출 데이터(전처리 전)")

# int화
df['결제 합계'] = int_format(df, '결제 합계')
df['매출'] = int_format(df, '매출')


# 메뉴명 매핑
menu_map = {
    '★매운가지치즈★솥밥': '매운가지치즈솥밥',
    '★우삼겹스키야키★': '우삼겹스키야키',
    '★매운가지치즈 ★ 더맵게': '매운가지치즈솥밥',
    '매운가지솥밥 더맵게': '매운가지솥밥',
    '매운가지치즈★솥밥': '매운가지치즈솥밥',
    '매운가지치즈 ★ 더맵게': '매운가지치즈솥밥',
    '매운가지치즈 ★더맵게x2': '매운가지치즈솥밥',
    '매운가지솥밥★더맵게': '매운가지솥밥',
    '★매운가지치즈★더맵게': '매운가지치즈솥밥',
    '매운가지솥밥☆더맵게x2': '매운가지솥밥',
    '★가지치즈★솥밥': '가지치즈솥밥',
    '매운가지치즈☆더맵게x2': '매운가지치즈솥밥',
    '테라 캔':'테라',
    '매운가지솥밥 더맵게x2':'매운가지솥밥',
    '★매운가지치즈 ★더맵게x2':'매운가지치즈솥밥'

}

df['상품명'] = df['상품명'].map(menu_map).fillna(df['상품명'])


# 메인 메뉴들만 필터링 후 일별 판매 데이터프레임 생성
df["판매일"] = pd.to_datetime(df["판매일시"]).dt.date
main_menu_list = ['가지솥밥', '꽈리고추두부솥밥', '마늘쫑솥밥', '매운가지솥밥', '매운가지치즈솥밥', '소고기숙주솥밥',
                  '스테이크솥밥', '연어솥밥', '우삼겹스키야키', '장어솥밥', '전복솥밥','가지치즈솥밥','우삼겹솥밥','고등어솥밥']

daily_sales = df[df['상품명'].isin(main_menu_list)]
daily_sales = (
    daily_sales.groupby(["판매일", "상품명"])
    .agg(
        일별수량=("수량", "sum"),
        일별매출=("매출", "sum")
    )
    .reset_index()
)

# 공통 결측일 탐색
unpopular_list = ["가지치즈솥밥", "우삼겹스키야키"]
new_list = ["우삼겹솥밥", "고등어솥밥"]
common_missing_dates = find_common_missing_dates(daily_sales, exclude_menus=unpopular_list+new_list) 

# 전체 보간 전처리 실행
all_results = preprocess_all_menus(
    daily_sales,
    unpopular_menus=unpopular_list,
    new_menus=new_list,
    common_missing_dates=common_missing_dates
)

all_df = pd.concat(all_results.values(), ignore_index=True)
all_values = [all_df.columns.tolist()] + all_df.astype(str).values.tolist()

# 업로드 실행
upload_to_sheet(
    key_path=key_path,
    sheet_id=sheet_id2,              
    sheet_name="결측치 보간",         
    values=all_values
)