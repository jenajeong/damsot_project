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
df = load_sheet_data(key_path, sheet_id2, "이상치 보간")

# 공통 결측일 탐색
unpopular_list = ["가지치즈솥밥", "우삼겹스키야키"]
new_list = ["우삼겹솥밥", "고등어솥밥"]
common_missing_dates = find_common_missing_dates(df, exclude_menus=unpopular_list+new_list) 

# 전체 보간 전처리 실행
all_results = preprocess_all_menus(
    df,
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
