import pandas as pd
from utils.data_set_get import load_sheet_data, load_config, upload_to_sheet
from utils.basic import int_format
from utils.outlier_utils import detect_outliers_by_iqr, replace_outliers_with_rolling_mean

# 필요한 정보 불러오기
key_path, sheet_id1, sheet_id2 = load_config()

# 시트 데이터 불러오기
df = load_sheet_data(key_path, sheet_id2, "총매출 데이터(전처리 전)")

# 숫자형 변환
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

# 메인 메뉴 필터링 후 일별 판매량 집계
df["판매일"] = pd.to_datetime(df["판매일시"]).dt.date
main_menu_list = [
    '가지솥밥', '꽈리고추두부솥밥', '마늘쫑솥밥', '매운가지솥밥', '매운가지치즈솥밥',
    '소고기숙주솥밥','스테이크솥밥', '연어솥밥', '우삼겹스키야키', '장어솥밥',
    '전복솥밥','가지치즈솥밥','우삼겹솥밥','고등어솥밥'
]

daily_sales = (
    df[df['상품명'].isin(main_menu_list)]
    .groupby(["판매일", "상품명"])
    .agg(일별수량=("수량", "sum"), 일별매출=("매출", "sum"))
    .reset_index()
)

# 이상치 탐지
outlier_summary = detect_outliers_by_iqr(daily_sales)

# 이상치 대체 (rolling mean, 이벤트일 제외)
cleaned = replace_outliers_with_rolling_mean(daily_sales, outlier_summary, window=3)

upload_to_sheet(
    key_path=key_path,
    sheet_id=sheet_id2,         
    sheet_name="이상치 대체",   
    values=[cleaned.columns.tolist()] + cleaned.astype(str).values.tolist()
)