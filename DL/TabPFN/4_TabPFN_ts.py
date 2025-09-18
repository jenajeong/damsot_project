import pandas as pd
import numpy as np
from tabpfn_time_series import TimeSeriesDataFrame, TabPFNTimeSeriesPredictor, TabPFNMode
from tabpfn_time_series.data_preparation import generate_test_X
from tabpfn_time_series.features import RunningIndexFeature, CalendarFeature, AutoSeasonalFeature
from tabpfn_time_series import FeatureTransformer
from utils.data_get import load_config, load_sheet_data


# 데이터 준비
key_path, sheet_id = load_config()
df = load_sheet_data(key_path, sheet_id, "날씨")
df["판매일"] = pd.to_datetime(df["판매일"])

# 특정 메뉴만 선택 (가지솥밥)
# menu = "가지솥밥"
# menu_df = df[df["상품명"] == menu].sort_values("판매일").reset_index(drop=True)

# item_id: 메뉴별 구분 (여러 메뉴 동시 예측 가능)
df["item_id"] = df["상품명"]

# TabPFN-TS 전용 포맷 만들기
tsdf = TimeSeriesDataFrame.from_data_frame(
    df,
    id_column="item_id",        # 개별 시계열 구분
    timestamp_column="판매일",   # 시간 컬럼
    target_column="일별수량"    # 예측할 값
)

# -----------------------------
# 2. Train/Test 분리
# -----------------------------
prediction_length = 7   # 앞으로 7일 예측
train_tsdf, test_tsdf_ground_truth = tsdf.train_test_split(prediction_length=prediction_length)
test_tsdf = generate_test_X(train_tsdf, prediction_length)

# -----------------------------
# 3. Feature 추가
# -----------------------------
selected_features = [
    RunningIndexFeature(),   # 단순 시계열 인덱스
    CalendarFeature(),       # 달력 기반 (요일, 월 등)
    AutoSeasonalFeature(),   # 자동 계절성
]

feature_transformer = FeatureTransformer(selected_features)
train_tsdf, test_tsdf = feature_transformer.transform(train_tsdf, test_tsdf)

# -----------------------------
# 4. TabPFN-TS 모델 학습 & 예측
# -----------------------------
predictor = TabPFNTimeSeriesPredictor(
    tabpfn_mode=TabPFNMode.LOCAL  # Colab API 쓰려면 CLIENT 모드 가능
)

pred = predictor.predict(train_tsdf, test_tsdf)

# -----------------------------
# 5. 시각화
# -----------------------------
from tabpfn_time_series.plot import plot_pred_and_actual_ts

plot_pred_and_actual_ts(
    train=train_tsdf,
    test=test_tsdf_ground_truth,
    pred=pred,
)