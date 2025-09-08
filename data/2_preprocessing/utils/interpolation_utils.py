import pandas as pd


# 공통의 미판매일 추출 (매장이 오픈하지 않은 날)
def find_common_missing_dates(daily_sales, exclude_menus=None):
    if exclude_menus is None:
        exclude_menus = []
    daily_sales["판매일"] = pd.to_datetime(daily_sales["판매일"])
    start_date = pd.to_datetime(daily_sales["판매일"].min())
    end_date = pd.to_datetime(daily_sales["판매일"].max())
    all_days = pd.date_range(start=start_date, end=end_date, freq="D")

    missing_sets = []

    for menu in daily_sales["상품명"].unique():
        if menu in exclude_menus:
            continue

        menu_daily = (
            daily_sales[daily_sales["상품명"] == menu]
            .groupby("판매일")["일별수량"]
            .sum()
            .reindex(all_days)
        )

        # NaN 날짜 추출
        missing_dates = set(menu_daily[menu_daily.isna()].index)
        missing_sets.append(missing_dates)

    # 모든 메뉴의 공통 미판매일
    if missing_sets:
        common_missing = set.intersection(*missing_sets)
    else:
        common_missing = set()

    return sorted(list(common_missing))


# 각 메뉴별 첫 번째 메뉴단가를 추출
def build_first_price_map(daily_sales):
    first_price_map = {}
    for menu, g in daily_sales.groupby("상품명"):
        g = g.sort_values("판매일")
        if not g.empty:
            first_price_map[menu] = g.iloc[0]["메뉴단가"]
        else:
            first_price_map[menu] = None
    return first_price_map


# 비인기메뉴 보간
def preprocess_unpopular_menu(df, menu_name, first_price_map):
    start_date = pd.to_datetime(df["판매일"]).min()
    end_date = pd.to_datetime(df["판매일"]).max()
    all_days = pd.date_range(start=start_date, end=end_date, freq="D")

    menu_df = (
        df[df["상품명"] == menu_name]
        .groupby("판매일")
        .agg(일별수량=("일별수량", "sum"))
        .reindex(all_days, fill_value=0)
    )

    menu_df = menu_df.reset_index().rename(columns={"index": "판매일"})
    menu_df["상품명"] = menu_name
    menu_df["메뉴단가"] = first_price_map.get(menu_name, None)
    return menu_df


# 신메뉴 보간
def preprocess_new_menu(df, menu_name, first_price_map):
    menu_data = df[df["상품명"] == menu_name]
    menu_start = pd.to_datetime(menu_data["판매일"].min())
    menu_end = pd.to_datetime(df["판매일"].max())
    all_days = pd.date_range(start=menu_start, end=menu_end, freq="D")

    menu_df = (
        menu_data.groupby("판매일")
        .agg(일별수량=("일별수량", "sum"))
        .reindex(all_days)
    )

    menu_df = menu_df.reset_index().rename(columns={"index": "판매일"})
    menu_df["상품명"] = menu_name
    menu_df["메뉴단가"] = first_price_map.get(menu_name, None)

    mask = menu_df["일별수량"].isna()
    if mask.sum() > 0:
        menu_df.loc[:, "일별수량"] = (
            menu_df["일별수량"].interpolate(method="linear").round().astype("Int64")
        )
    else:
        print(f"[INFO] '{menu_name}'에는 보간할 NaN 없음")

    return menu_df


# 메인메뉴들 보간
def preprocess_main_menu(daily_sales, first_price_map, exclude_menus=None, common_missing_dates=None):
    if exclude_menus is None:
        exclude_menus = []
    if common_missing_dates is None:
        common_missing_dates = []

    start_date = pd.to_datetime(daily_sales["판매일"].min())
    end_date = pd.to_datetime(daily_sales["판매일"].max())
    all_days = pd.date_range(start=start_date, end=end_date, freq="D")

    results = {}
    for menu in daily_sales["상품명"].unique():
        if menu in exclude_menus:
            print(f"[SKIP] {menu} 제외됨")
            continue

        menu_data = daily_sales[daily_sales["상품명"] == menu]
        menu_df = (
            menu_data.groupby("판매일")
            .agg(일별수량=("일별수량", "sum"))
            .reindex(all_days)
        )
        menu_df = menu_df.reset_index().rename(columns={"index": "판매일"})
        menu_df["상품명"] = menu
        menu_df["메뉴단가"] = first_price_map.get(menu, None)

        # 공통 결측일 → 0
        mask_common = menu_df["판매일"].isin(common_missing_dates)
        menu_df.loc[mask_common, "일별수량"] = 0

        # 나머지 NaN 보간
        mask_other = menu_df["일별수량"].isna()
        if mask_other.sum() > 0:
            interpolated_qty = menu_df["일별수량"].interpolate(method="linear").round()
            menu_df.loc[mask_other, "일별수량"] = interpolated_qty[mask_other]

        results[menu] = menu_df

    return results


# 전체 보간 실행 로직
def preprocess_all_menus(daily_sales, unpopular_menus, new_menus, first_price_map, common_missing_dates=None):
    results = {}

    # 비인기 메뉴
    for menu in unpopular_menus:
        print(f"[PROCESS-UNPOPULAR] {menu}")
        results[menu] = preprocess_unpopular_menu(daily_sales, menu, first_price_map)

    # 신메뉴
    for menu in new_menus:
        print(f"[PROCESS-NEW] {menu}")
        results[menu] = preprocess_new_menu(daily_sales, menu, first_price_map)

    # 메인 메뉴
    exclude_menus = unpopular_menus + new_menus
    main_results = preprocess_main_menu(
        daily_sales, first_price_map, exclude_menus=exclude_menus, common_missing_dates=common_missing_dates
    )
    results.update(main_results)

    return results
