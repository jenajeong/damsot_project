import pandas as pd
import matplotlib.pyplot as plt
from tabpfn import TabPFNRegressor
from utils.data_get import load_config, load_sheet_data
from sklearn.preprocessing import StandardScaler

# 데이터 준비
key_path, sheet_id = load_config()
df = load_sheet_data(key_path, sheet_id, "날씨")
df["판매일"] = pd.to_datetime(df["판매일"])

# 특정 메뉴만 선택 (가지솥밥)
menu = "가지솥밥"
menu_df = df[df["상품명"] == menu].sort_values("판매일").reset_index(drop=True)

# ✅ lag 피처 생성
menu_df["lag1"] = menu_df["일별수량"].shift(1)
menu_df["lag2"] = menu_df["일별수량"].shift(2)
menu_df["lag7"] = menu_df["일별수량"].shift(7)

# NaN 제거 (초반부 몇 개는 제거됨)
menu_df = menu_df.dropna().reset_index(drop=True)

# 사용할 feature들
features = ["메뉴단가", "요일_sin", "요일_cos", "lag1", "lag2", "lag7"]

# 마지막 7일 롤링 예측
preds, actuals, dates = [], [], []

train_size = len(menu_df) - 7

for i in range(7):
    # 학습 데이터 (처음 ~ test 시작점 - 1)
    X_train = menu_df.iloc[:train_size+i][features]
    y_train = menu_df.iloc[:train_size+i]["일별수량"]

    # 예측할 데이터 (train 이후 한 칸)
    X_test = menu_df.iloc[[train_size+i]][features]
    y_test = menu_df.iloc[train_size+i]["일별수량"]
    date = menu_df.iloc[train_size+i]["판매일"]

    # 모델 학습 & 예측
    model = TabPFNRegressor() # 반복해서 데이터를 넣으면 안된다길래 계속 리셋
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)[0]

    # 결과 저장
    preds.append(y_pred)
    actuals.append(y_test)
    dates.append(date)

# 결과 출력
results = pd.DataFrame({"판매일": dates, "실제값": actuals, "예측값": preds})
print(results)

# 시각화
plt.figure(figsize=(10, 5))
plt.plot(results["판매일"], results["실제값"], marker="o", label="실제값")
plt.plot(results["판매일"], results["예측값"], marker="s", label="예측값")
plt.xticks(rotation=45)
plt.title("predict - rollong forcast last 7 days")
plt.xlabel("sales date")
plt.ylabel("daily count")
plt.legend()
plt.tight_layout()
plt.show()
