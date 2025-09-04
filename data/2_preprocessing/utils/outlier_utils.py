import pandas as pd
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

    date_counts = Counter()
    menu_outliers = defaultdict(list)

    # 메뉴별 이상치 모으기
    for _, row in outlier_summary.iterrows():
        menu = row["메뉴"]
        for date, val in row["이상치 상세"]:
            d = pd.to_datetime(date).date()
            date_counts[d] += 1
            menu_outliers[menu].append((d, val))

    cleaned = daily_sales.copy()
    cleaned["판매일"] = pd.to_datetime(cleaned["판매일"])

    # 메뉴별로 rolling mean 계산 후 이상치 처리
    for menu, outliers in menu_outliers.items():
        subset = cleaned[cleaned["상품명"] == menu].sort_values("판매일").copy()
        subset["rolling_mean"] = subset["일별수량"].rolling(
            window=window, center=True, min_periods=1
        ).mean()

        for d, val in outliers:
            if date_counts[d] >= 2:   # 이벤트일 → 유지
                continue

            # cleaned에서 직접 마스크 생성
            mask = (cleaned["상품명"] == menu) & (cleaned["판매일"].dt.date == d)
            if not mask.any():
                continue

            old_qty = cleaned.loc[mask, "일별수량"].values[0]
            old_sales = cleaned.loc[mask, "일별매출"].values[0]

            roll_val = subset.loc[subset["판매일"].dt.date == d, "rolling_mean"].values[0]

            if pd.isna(roll_val):
                # NaN은 그대로 두기 → 이후 interpolate로 처리
                cleaned.loc[mask, "일별수량"] = np.nan
                cleaned.loc[mask, "일별매출"] = np.nan
            else:
                new_qty = round(roll_val)
                unit_price = old_sales / old_qty if old_qty != 0 else 0
                new_sales = new_qty * unit_price

                cleaned.loc[mask, "일별수량"] = new_qty
                cleaned.loc[mask, "일별매출"] = new_sales

    return cleaned
