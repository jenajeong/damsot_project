import pandas as pd
from utils.basic import int_format, trim_to_yesterday
from utils.data_set_get import load_config, load_sheet_data, upload_to_sheet

# 필요한 정보 불러오기
key_path, sheet_id1, sheet_id2 = load_config()
df = load_sheet_data(key_path, sheet_id2, "총매출 데이터(전처리 전)")

# # 메뉴명 매핑
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
    '★매운가지치즈 ★더맵게x2':'매운가지치즈솥밥',
    '@가지치즈솥밥@' : '가지치즈솥밥',
    '@매운가지치즈솥밥@' : '매운가지치즈솥밥' 
}
df['상품명'] = df['상품명'].map(menu_map).fillna(df['상품명'])

fin_df = df[['판매일시','테이블코드','타입','결제 합계','상품명','상품코드','수량','매출','공급가액','부가세']]
fin_values = fin_df.astype(str).values.tolist()

upload_to_sheet(
    key_path=key_path,
    sheet_id=sheet_id2,
    sheet_name="총매출 데이터",
    values=fin_values
)








