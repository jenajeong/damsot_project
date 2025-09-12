import pygsheets
import requests
import pandas as pd
import io
from utils.data_set_get import load_config, upload_to_sheet, load_sheet_data

# API 설정
key_path, sheet_id, ASOS_API, BASE_URL = load_config()
stn_id = "104"  # 서울

# 요청 기간
tm1 = "20240823"
tm2 = "20250831"

# API 요청 URL
url = f"{BASE_URL}?tm1={tm1}&tm2={tm2}&stn={stn_id}&authKey={ASOS_API}"

response = requests.get(url)
raw_text = response.text

# 주석(#) 제거 + END 제거
lines = raw_text.splitlines()
clean_lines = [line for line in lines if not line.startswith("#") and "END" not in line]

# DataFrame 생성
weather = pd.read_csv(io.StringIO("\n".join(clean_lines)), delim_whitespace=True, header=None)

colnames = [
    "TM", "STN", "WS_AVG", "WR_DAY", "WD_MAX", "WS_MAX", "WS_MAX_TM",
    "WD_INS", "WS_INS", "WS_INS_TM", "TA_AVG", "TA_MAX", "TA_MAX_TM",
    "TA_MIN", "TA_MIN_TM", "TD_AVG", "TS_AVG", "TG_MIN", "HM_AVG",
    "HM_MIN", "HM_MIN_TM", "PV_AVG", "EV_S", "EV_L", "FG_DUR",
    "PA_AVG", "PS_AVG", "PS_MAX", "PS_MAX_TM", "PS_MIN", "PS_MIN_TM",
    "CA_TOT", "SS_DAY", "SS_DUR", "SS_CMB", "SI_DAY", "SI_60M_MAX",
    "SI_60M_MAX_TM", "RN_DAY", "RN_D99", "RN_DUR", "RN_60M_MAX",
    "RN_60M_MAX_TM", "RN_10M_MAX", "RN_10M_MAX_TM", "RN_POW_MAX",
    "RN_POW_MAX_TM", "SD_NEW", "SD_NEW_TM", "SD_MAX", "SD_MAX_TM",
    "TE_05", "TE_10", "TE_15", "TE_30", "TE_50"
]
weather.columns = colnames

# 날짜 형식 변환
weather["날짜"] = pd.to_datetime(weather["날짜"], format="%Y%m%d")

weather_sel = weather[[
    "TM",        # 날짜
    "TA_AVG",    # 평균기온
    "TA_MAX",    # 최고기온
    "TA_MIN",    # 최저기온
    "HM_AVG",    # 평균습도
    "WS_AVG",    # 평균풍속
    "SS_DAY",    # 일조 시간
    "SI_DAY",    # 일사량
    "CA_TOT"     # 전운량
]].copy()


# 1. 날씨 컬럼명 보기 좋게 바꾸기
weather_df = weather_sel.rename(columns={
    "TA_AVG": "평균기온",
    "TA_MAX": "최고기온",
    "TA_MIN": "최저기온",
    "HM_AVG": "평균습도",
    "WS_AVG": "평균풍속",
    "TM": "판매일",
    "SS_DAY":"일조합",
    "SI_DAY":"일사합",
    "CA_TOT":"전운량"
})

# 데이터 불러오기
df = load_sheet_data(key_path, sheet_id, "요일")


# 2. 날짜 형식 통일 (문자열 → datetime)
df["판매일"] = pd.to_datetime(df["판매일"])
weather_df["판매일"] = pd.to_datetime(weather_df["판매일"], format="%Y%m%d")

merged_df = pd.merge(df, weather_df, on="판매일", how="inner")

all_values = merged_df.astype(str).values.tolist()

# 업로드 실행
upload_to_sheet(
    key_path=key_path,
    sheet_id=sheet_id,              
    sheet_name="날씨",         
    values=all_values
)
