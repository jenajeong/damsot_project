import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import torch as t
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt
import tensorflow as tf
import os
import json
# ================================
# 1. 데이터 로드 & 전처리
# ================================
BASE_DIR = os.path.dirname(os.path.abspath(file))
json_path = os.path.join(BASE_DIR, "damsot.json")

with open(json_path, "r", encoding="utf-8") as f:
    info = json.load(f)

key_path = os.path.join(BASE_DIR, info['key_path'])
SPREAD_ID = info['SPREAD_ID']

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]


creds = Credentials.from_service_account_file(KEY_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)

# "날씨" 시트
ws = gc.open_by_key(SPREAD_ID).worksheet("날씨")
values = ws.get_all_values()
feat = pd.DataFrame(values[1:], columns=values[0])
feat["판매일"] = pd.to_datetime(feat["판매일"], errors="coerce")

num_cols = ["일별수량","메뉴단가","요일","요일_sin","요일_cos",
            "평균기온","최고기온","최저기온","평균습도","평균풍속","일조합","일사합","전운량"]
for c in num_cols:
    if c in feat.columns:
        feat[c] = pd.to_numeric(feat[c].astype(str).str.replace(",", "").str.replace("%",""),
                               errors="coerce")

feat = feat.sort_values("판매일").reset_index(drop=True)

# "상품명 임베딩" 시트 불러오기
ws_embedding = gc.open_by_key(SPREAD_ID).worksheet("상품명 임베딩")
values_embedding = ws_embedding.get_all_values()
embedding_df = pd.DataFrame(values_embedding[1:], columns=values_embedding[0])

# 병합 (모든 메뉴 사용)
feat_im = feat.merge(embedding_df, on="상품명", how="left")

# 컬럼 정리 (_x, _y 제거)
def _normalize_merged_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {c: c[:-2] for c in df.columns if c.endswith('_x')}
    df = df.rename(columns=rename_map)
    drop_cols = [c for c in df.columns if c.endswith('_y') and c[:-2] in df.columns]
    return df.drop(columns=drop_cols, errors='ignore')

feat_im = _normalize_merged_columns(feat_im)

# 스케일링
columns_to_scale = ['일별수량', '메뉴단가', '평균기온', '최고기온', '최저기온']
scaler = MinMaxScaler()
feat_cleaned = feat_im.copy()
cols_existing = [c for c in columns_to_scale if c in feat_cleaned.columns]
feat_cleaned.loc[:, cols_existing] = scaler.fit_transform(feat_cleaned[cols_existing])
feat_cleaned = feat_cleaned.dropna().reset_index(drop=True)

# 역정규화용 타깃 스케일
target_col = '일별수량'
target_idx_in_scale = cols_existing.index(target_col)
target_min = scaler.data_min_[target_idx_in_scale]
target_max = scaler.data_max_[target_idx_in_scale]

# ================================
# 2. 슬라이딩 윈도우 분할
# ================================
# 외생변수에 임베딩 포함
embedding_cols = [c for c in feat_cleaned.columns if "임베딩" in c]
features = ['메뉴단가', '요일_sin', '요일_cos', '평균기온', '최고기온', '최저기온'] + embedding_cols

target_series = feat_cleaned['일별수량'].values.reshape(-1, 1)
eps = 1e-8
target_series = np.where(target_series == 0, eps, target_series)
exo_matrix = feat_cleaned[features].values

window_size = 28
forecast_length = 1

def sliding_window_split_multi(target, exo, window_size, forecast_length):
    X_t, X_e, y = [], [], []
    for i in range(len(target) - window_size - forecast_length + 1):
        X_t.append(target[i:i + window_size])
        X_e.append(exo[i:i + window_size])
        y.append(target[i + window_size:i + window_size + forecast_length])
    return np.array(X_t), np.array(X_e), np.array(y)

num_rows = len(feat_cleaned)
train_end = int(num_rows * 0.70)
val_end = int(num_rows * 0.85)

X_t_train, X_e_train, y_train = sliding_window_split_multi(
    target_series[:train_end], exo_matrix[:train_end], window_size, forecast_length)
X_t_val, X_e_val, y_val = sliding_window_split_multi(
    target_series[train_end:val_end], exo_matrix[train_end:val_end], window_size, forecast_length)
X_t_test, X_e_test, y_test = sliding_window_split_multi(
    target_series[val_end:], exo_matrix[val_end:], window_size, forecast_length)

# 분할 결과 확인 및 가드
print(f"윈도우 분할 결과 -> X_tr:{X_t_train.shape}, X_e_tr:{X_e_train.shape}, y_tr:{y_train.shape}")
print(f"                    X_va:{X_t_val.shape}, X_e_va:{X_e_val.shape}, y_va:{y_val.shape}")
print(f"                    X_te:{X_t_test.shape}, X_e_te:{X_e_test.shape}, y_te:{y_test.shape}")
if any(arr.shape[0] == 0 for arr in [X_t_train, y_train, X_t_val, y_val, X_t_test, y_test]):
    raise ValueError("윈도우 분할 결과가 비었습니다. window_size/forecast_length/데이터 길이를 확인하세요.")

# ================================
# 3. PyTorch N-BEATS (Global Input)
# ================================
class GenericBasis(t.nn.Module):
    def __init__(self, backcast_size: int, forecast_size: int):
        super().__init__()
        self.backcast_size = backcast_size
        self.forecast_size = forecast_size
    def forward(self, theta: t.Tensor):
        return theta[:, :self.backcast_size], theta[:, -self.forecast_size:]

class NBeatsBlock(t.nn.Module):
    def __init__(self, input_size: int, theta_size: int, basis_function: t.nn.Module, layers: int, layer_size: int):
        super().__init__()
        self.layers = t.nn.ModuleList([t.nn.Linear(input_size, layer_size)] +
                                      [t.nn.Linear(layer_size, layer_size) for _ in range(layers - 1)])
        self.basis_parameters = t.nn.Linear(layer_size, theta_size)
        self.basis_function = basis_function
    def forward(self, x: t.Tensor):
        for layer in self.layers:
            x = t.relu(layer(x))
        theta = self.basis_parameters(x)
        return self.basis_function(theta)

class NBeats(t.nn.Module):
    def __init__(self, blocks: t.nn.ModuleList):
        super().__init__()
        self.blocks = blocks
    def forward(self, x: t.Tensor) -> t.Tensor:
        residuals = t.flip(x, dims=(1,))
        forecast = x[:, -1:]
        for block in self.blocks:
            backcast, block_forecast = block(residuals)
            residuals = residuals - backcast
            forecast = forecast + block_forecast
        return forecast

class WindowDataset(Dataset):
    def __init__(self, X_t: np.ndarray, X_e: np.ndarray, y: np.ndarray):
        # 👉 X_t와 X_e를 하나로 합쳐 global input으로 사용
        X_cat = np.concatenate([X_t.squeeze(-1), X_e.mean(axis=1)], axis=1)  # 단순화: 외생 평균
        self.X = t.tensor(X_cat, dtype=t.float32)
        self.y = t.tensor(y, dtype=t.float32)
    def __len__(self):
        return len(self.X)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# ================================
# 4. 학습 루프
# ================================
device = t.device('cuda' if t.cuda.is_available() else 'cpu')

train_loader = DataLoader(WindowDataset(X_t_train, X_e_train, y_train), batch_size=64, shuffle=False)
val_loader = DataLoader(WindowDataset(X_t_val, X_e_val, y_val), batch_size=64, shuffle=False)
test_loader = DataLoader(WindowDataset(X_t_test, X_e_test, y_test), batch_size=64, shuffle=False)

backcast, forecast = window_size + X_e_train.shape[2], forecast_length
theta_size = backcast + forecast
blocks = t.nn.ModuleList([
    NBeatsBlock(backcast, theta_size, GenericBasis(backcast, forecast), layers=4, layer_size=256),
    NBeatsBlock(backcast, theta_size, GenericBasis(backcast, forecast), layers=4, layer_size=256),
    NBeatsBlock(backcast, theta_size, GenericBasis(backcast, forecast), layers=4, layer_size=256)
])
model_t = NBeats(blocks).to(device)
optimizer = t.optim.Adam(model_t.parameters(), lr=1e-3)
criterion = t.nn.MSELoss()

best_val, patience, wait = float('inf'), 10, 0
for epoch in range(100):
    model_t.train()
    train_loss = 0.0
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()
        loss = criterion(model_t(xb), yb)
        loss.backward()
        optimizer.step()
        train_loss += loss.item() * xb.size(0)
    train_loss /= len(train_loader.dataset)

    model_t.eval()
    val_loss = 0.0
    with t.no_grad():
        for xb, yb in val_loader:
            xb, yb = xb.to(device), yb.to(device)
            val_loss += criterion(model_t(xb), yb).item() * xb.size(0)
    val_loss /= len(val_loader.dataset)

    print(f"[Epoch {epoch+1}] train={train_loss:.5f} val={val_loss:.5f}")
    if val_loss < best_val - 1e-6:
        best_val, best_state, wait = val_loss, {k: v.cpu() for k, v in model_t.state_dict().items()}, 0
    else:
        wait += 1
        if wait >= patience:
            print("Early stopping.")
            break

model_t.load_state_dict(best_state)
model_t.eval()

# ================================
# 5. 평가 및 시각화
# ================================
def predict_loader(loader):
    ys, yhats = [], []
    with t.no_grad():
        for xb, yb in loader:
            yhats.append(model_t(xb.to(device)).cpu().numpy())
            ys.append(yb.numpy())
    return np.concatenate(ys, axis=0), np.concatenate(yhats, axis=0)

y_train_np, y_pred_train = predict_loader(train_loader)
y_val_np, y_pred_val = predict_loader(val_loader)
y_test_np, y_pred_test = predict_loader(test_loader)

def inv_scale(x):
    return x * (target_max - target_min) + target_min

y_train_inv, y_val_inv, y_test_inv = map(inv_scale, [y_train_np, y_val_np, y_test_np])
y_pred_train_inv = inv_scale(np.clip(y_pred_train, 0.0, 1.0))
y_pred_val_inv = inv_scale(np.clip(y_pred_val, 0.0, 1.0))
y_pred_test_inv = inv_scale(np.clip(y_pred_test, 0.0, 1.0))

def smape(y_true, y_pred, eps=1e-8):
    y_true = tf.convert_to_tensor(y_true, dtype=tf.float32)
    y_pred = tf.convert_to_tensor(y_pred, dtype=tf.float32)
    numerator = tf.abs(y_pred - y_true)
    denominator = (tf.abs(y_true) + tf.abs(y_pred)) / 2.0 + eps
    return tf.reduce_mean(numerator / denominator) * 100

train_smape_val = smape(y_train_inv, y_pred_train_inv).numpy()
val_smape_val = smape(y_val_inv, y_pred_val_inv).numpy()
test_smape_val = smape(y_test_inv, y_pred_test_inv).numpy()

print(f"\nTrain sMAPE: {train_smape_val:.3f}")
print(f"Validation sMAPE: {val_smape_val:.3f}")
print(f"Test sMAPE: {test_smape_val:.3f}")

plt.figure(figsize=(12,5))
plt.plot(y_test_inv[-100:], label="True")
plt.plot(y_pred_test_inv[-100:], label="Pred")
plt.grid(True, alpha=0.3)
plt.title(f"Global N-BEATS 수요예측 (Test sMAPE: {test_smape_val:.2f}%)")
plt.xlabel("Step")
plt.ylabel("Demand")
plt.legend()
plt.tight_layout()
out_path = "/Users/mac/Desktop/담솥/forecast_plot_global.png"
plt.savefig(out_path, dpi=150)
print(f"그래프 저장: {out_path}")
plt.close()
