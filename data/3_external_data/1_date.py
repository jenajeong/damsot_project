import pygsheets
import pandas as pd
import numpy as np
from utils.data_set_get import load_config, upload_to_sheet, load_sheet_data

key_path, sheet_id, ASOS_API, BASE_URL = load_config()
df = load_sheet_data(key_path, sheet_id, "결측치 보간")

# 요일 추출 (월=0, 일=6)
df["판매일"] = pd.to_datetime(df["판매일"])
df["요일"] = df["판매일"].dt.dayofweek

df["요일_sin"] = np.sin(2 * np.pi * df["요일"] / 7)
df["요일_cos"] = np.cos(2 * np.pi * df["요일"] / 7)

all_values = df.astype(str).values.tolist()

# 업로드 실행
upload_to_sheet(
    key_path=key_path,
    sheet_id=sheet_id,              
    sheet_name="요일",         
    values=all_values
)
