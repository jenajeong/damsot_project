import pandas as pd
import matplotlib.pyplot as plt
from utils.data_get import load_config, load_sheet_data
from sklearn.metrics import accuracy_score, classification_report
from tabpfn import TabPFNClassifier
import numpy as np

# 데이터 준비
key_path, sheet_id = load_config()
df = load_sheet_data(key_path, sheet_id, "날씨")
df["판매일"] = pd.to_datetime(df["판매일"])

# 특정 메뉴만 선택 (가지솥밥)
menu = "가지솥밥"
menu_df = df[df["상품명"] == menu].sort_values("판매일").reset_index(drop=True)

menu_df["lag1"] = menu_df["일별수량"].shift(1)
menu_df["lag2"] = menu_df["일별수량"].shift(2)
menu_df["lag7"] = menu_df["일별수량"].shift(7)

menu_df = menu_df.dropna().reset_index(drop=True)

# y를 3개 단위 구간으로 변환
def bucketize_qty(y):
    return np.select(
        [y == 0, (y >= 1) & (y <= 5), (y >= 6) & (y <= 10),
         (y >= 11) & (y <= 20), (y >= 21) & (y <= 30), (y >= 31) & (y <= 40) , (y >= 41) & (y <= 50)
         ,(y >= 51) & (y <= 60), y > 60],
        [0, 1, 2, 3, 4, 5,6,7,8]
    )

# 예시: 데이터 준비
X = menu_df[["메뉴단가", "요일_sin", "요일_cos", "lag1", "lag2", "lag7"]]  # feature
y = bucketize_qty(menu_df["일별수량"].values)

# Train/test split (마지막 7일을 test)
X_train, X_test = X.iloc[:-7], X.iloc[-7:]
y_train, y_test = y[:-7], y[-7:]

# 모델 학습
clf = TabPFNClassifier(device="cpu")
clf.fit(X_train, y_train)

# 예측
preds = clf.predict(X_test)

# 평가
print("Accuracy:", accuracy_score(y_test, preds))
print(classification_report(y_test, preds))

# 결과 확인
results = pd.DataFrame({
    "판매일": menu_df["판매일"].iloc[-7:].values,
    "실제클래스": y_test,
    "예측클래스": preds
})
print(results)

# 시각화
plt.figure(figsize=(10, 5))
plt.plot(results["판매일"], results["실제값"], marker="o", label="실제값")
plt.plot(results["판매일"], results["예측값"], marker="s", label="예측값")
plt.xticks(rotation=45)
plt.title("Classifier predict -  last 7 days")
plt.xlabel("sales date")
plt.ylabel("daily count")
plt.legend()
plt.tight_layout()
plt.show()
