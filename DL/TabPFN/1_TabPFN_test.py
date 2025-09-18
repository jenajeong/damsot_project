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

# feature/target 정의
features = ["메뉴단가", "요일_cos", "평균기온",'최고기온','최저기온','평균습도','평균풍속','일조합','일사합','전운량']

# 결과 저장
results = []

# 마지막 7일 롤링 예측
for i in range(7):
    # 학습 데이터: 처음 ~ (마지막7일 시작+i - 1)
    train_end = len(menu_df) - 7 + i
    test_idx = train_end
    
    X_train = menu_df.iloc[:train_end][features]
    y_train = menu_df.iloc[:train_end]["일별수량"]
    
    X_test = menu_df.iloc[[test_idx]][features]
    y_test = menu_df.iloc[test_idx]["일별수량"]
    
    # TabPFN 모델
    model = TabPFNRegressor()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)[0]
    
    results.append({
        "판매일": menu_df.iloc[test_idx]["판매일"],
        "실제값": y_test,
        "예측값": y_pred
    })

# DataFrame 변환
pred_df = pd.DataFrame(results)

# 결과 출력
print(pred_df)

# 시각화
plt.figure(figsize=(10, 5))
plt.plot(pred_df["판매일"], pred_df["실제값"], marker="o", label="실제값")
plt.plot(pred_df["판매일"], pred_df["예측값"], marker="s", label="예측값")
plt.xticks(rotation=45)
plt.title("predict - rollong forcast last 7 days")
plt.xlabel("sales date")
plt.ylabel("daily count")
plt.legend()
plt.tight_layout()
plt.show()
