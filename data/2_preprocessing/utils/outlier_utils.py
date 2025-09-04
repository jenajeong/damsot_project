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

def replace_outliers_with_rolling_mean(daily_sales, outlier_summary, window):
    
    date_counts = Counter()
    menu_outliers = defaultdict(list)

    for _, row in outlier_summary.iterrows():
        menu = row["메뉴"]
        for date, val in row["이상치 상세"]:
            d = pd.to_datetime(date).date()
            date_counts[d] += 1
            menu_outliers[menu].append((d, val))

    cleaned = daily_sales.copy()
    cleaned["판매일"] = pd.to_datetime(cleaned["판매일"])

    for menu, outliers in menu_outliers.items():
        subset = cleaned[cleaned["상품명"] == menu].sort_values("판매일").copy()
        subset["rolling_mean"] = subset["일별수량"].rolling(
            window=window, center=True, min_periods=1
        ).mean() # 기준일로 앞,뒤 3일을 평균

        for d, val in outliers:
            if date_counts[d] >= 2:   # 2개 이상은 이벤트일로, 필연으로 생각하여 대치X
                continue
            idx = (subset["판매일"].dt.date == d)
            if idx.any():
                old_qty = subset.loc[idx, "일별수량"].values[0]
                old_sales = subset.loc[idx, "일별매출"].values[0]
                new_qty = round(subset.loc[idx, "rolling_mean"].values[0])
                unit_price = old_sales / old_qty if old_qty != 0 else 0
                new_sales = new_qty * unit_price

                cleaned.loc[
                    (cleaned["상품명"] == menu) & (cleaned["판매일"].dt.date == d), "일별수량"
                ] = new_qty
                cleaned.loc[
                    (cleaned["상품명"] == menu) & (cleaned["판매일"].dt.date == d), "일별매출"
                ] = new_sales

    return cleaned