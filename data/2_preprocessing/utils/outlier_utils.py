import pandas as pd
import numpy as np
from collections import Counter, defaultdict

def detect_outliers_by_iqr(df):
    """
    메뉴별로 IQR 기준 이상치를 탐지하고 기초 통계량과 함께 반환
    """
    results = []
    for menu, subset in df.groupby("상품명"):
        q1 = subset['일별수량'].quantile(0.25)
        q3 = subset['일별수량'].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = subset[(subset['일별수량'] < lower) | (subset['일별수량'] > upper)][['판매일','일별수량']]
        stats = subset['일별수량'].describe()

        results.append({
            "메뉴": menu,
            "count": int(stats["count"]),
            "mean": round(stats["mean"], 2),
            "std": round(stats["std"], 2),
            "min": int(stats["min"]),
            "25%": int(stats["25%"]),
            "50%": int(stats["50%"]),
            "75%": int(stats["75%"]),
            "max": int(stats["max"]),
            "이상치 개수": len(outliers),
            "이상치 상세": outliers.values.tolist() 
        })
    return pd.DataFrame(results)

def replace_outliers_with_rolling_mean(daily_sales, outlier_summary, window=3):
    # 0) 준비
    cleaned = daily_sales.copy()
    cleaned["판매일"] = pd.to_datetime(cleaned["판매일"])

    # 1) 메뉴별 '첫 유효 오더' 단가 맵 (수량>0 & 매출>0 중 가장 이른 날짜)
    df = cleaned.copy()
    first_price_map = {}
    for menu, g in df.groupby("상품명"):
        g = g[(g["일별수량"] > 0) & (g["일별매출"] > 0)].sort_values("판매일")
        if not g.empty:
            first_price_map[menu] = float(g.iloc[0]["일별매출"]) / float(g.iloc[0]["일별수량"])
        else:
            first_price_map[menu] = np.nan  # 유효 판매가 없는 메뉴면 단가 없음

    # 2) outlier 요약 정리
    date_counts = Counter()
    menu_outliers = defaultdict(list)
    for _, row in outlier_summary.iterrows():
        menu = row["메뉴"]
        for date, val in row["이상치 상세"]:
            d = pd.to_datetime(date).date()
            date_counts[d] += 1
            menu_outliers[menu].append((d, val))

    # 3) 메뉴별로 rolling mean 수량 보정만 수행
    for menu, outliers in menu_outliers.items():
        subset = cleaned[cleaned["상품명"] == menu].sort_values("판매일").copy()
        subset["rolling_mean"] = subset["일별수량"].rolling(
            window=window, center=True, min_periods=1
        ).mean()

        for d, _ in outliers:
            # 이벤트일(같은 날짜 이상치 2개 이상)은 건드리지 않음
            if date_counts[d] >= 2:
                continue

            mask = (cleaned["상품명"] == menu) & (cleaned["판매일"].dt.date == d)
            if not mask.any():
                continue

            roll_vals = subset.loc[subset["판매일"].dt.date == d, "rolling_mean"]
            roll_val = roll_vals.iloc[0] if not roll_vals.empty else np.nan

            if pd.isna(roll_val):
                cleaned.loc[mask, "일별수량"] = np.nan
                continue

            new_qty = int(round(max(0, roll_val)))
            cleaned.loc[mask, "일별수량"] = new_qty

    # 4) 메뉴단가 컬럼 추가 (모든 행에 매핑)
    cleaned["메뉴단가"] = cleaned["상품명"].map(first_price_map)

    return cleaned
