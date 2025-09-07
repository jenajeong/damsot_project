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




# 비인기메뉴 보간
def preprocess_unpopular_menu(df, menu_name):
    # 전체 구간
    start_date = pd.to_datetime(df["판매일"]).min()
    end_date = pd.to_datetime(df["판매일"]).max()
    all_days = pd.date_range(start=start_date, end=end_date, freq="D")

    # 특정 메뉴만 추출 후 집계
    menu_df = (
        df[df["상품명"] == menu_name]
        .groupby("판매일")
        .agg(
            일별수량=("일별수량", "sum"),
            일별매출=("일별매출", "sum")
        )
        .reindex(all_days, fill_value=0)   # 전체 구간에 맞춰서 0으로 채움
    )

    # 정리
    menu_df = menu_df.reset_index().rename(columns={"index": "판매일"})
    menu_df["상품명"] = menu_name

    return menu_df



# 신메뉴 보간
def preprocess_new_menu(df, menu_name):
    menu_data = df[df["상품명"] == menu_name]

    # 신메뉴의 판매개시일부터 전체마지막 판매일
    menu_start = pd.to_datetime(menu_data["판매일"].min())
    menu_end = pd.to_datetime(df["판매일"].max())
    all_days = pd.date_range(start=menu_start, end=menu_end, freq="D")

    # 메뉴 집계
    menu_df = (
        menu_data.groupby("판매일")
        .agg(일별수량=("일별수량", "sum"), 일별매출=("일별매출", "sum"))
        .reindex(all_days)
    )

    menu_df = menu_df.reset_index().rename(columns={"index": "판매일"})
    menu_df["상품명"] = menu_name

    # 단가 계산
    unit_price = round(menu_data["일별매출"].sum() / menu_data["일별수량"].sum())

    # 보간 대상 마스크 (원래 NaN이었던 row)
    mask = menu_df["일별수량"].isna()
    nan_count = mask.sum()

    if nan_count > 0:
        # 보간 후 정수화
        menu_df.loc[:, "일별수량"] = (
            menu_df["일별수량"]
            .interpolate(method="linear")
            .round()
            .astype("Int64")
        )

        # 원래 NaN이었던 로우만 매출 재계산
        menu_df.loc[mask, "일별매출"] = menu_df.loc[mask, "일별수량"] * unit_price
    else:
        print(f"[INFO] '{menu_name}'에는 보간할 NaN 값이 없음")

    return menu_df



# 메인메뉴들 보간
def preprocess_main_menu(daily_sales, exclude_menus=None, common_missing_dates=None):
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

        # 메뉴 데이터 추출
        menu_data = daily_sales[daily_sales["상품명"] == menu]

        # 일별 집계 후 전체 구간 확장
        menu_df = (
            menu_data.groupby("판매일")
            .agg(일별수량=("일별수량", "sum"), 일별매출=("일별매출", "sum"))
            .reindex(all_days)
        )
        menu_df = menu_df.reset_index().rename(columns={"index": "판매일"})
        menu_df["상품명"] = menu

        # 단가 계산
        unit_price = round(menu_data["일별매출"].sum() / menu_data["일별수량"].sum())

        # 1️⃣ 모든 메뉴 공통 결측일 → 0으로 확정
        mask_common = menu_df["판매일"].isin(common_missing_dates)
        menu_df.loc[mask_common, "일별수량"] = 0
        menu_df.loc[mask_common, "일별매출"] = 0

        # 2️⃣ 그 외 NaN만 보간 (수량 → 정수 변환)
        mask_other = menu_df["일별수량"].isna()
        if mask_other.sum() > 0:
            # 보간 후 float로 유지
            interpolated_qty = (
                menu_df["일별수량"]
                .interpolate(method="linear")
                .round()
            )

            menu_df.loc[mask_other, "일별수량"] = interpolated_qty[mask_other]
            menu_df.loc[mask_other, "일별매출"] = menu_df.loc[mask_other, "일별수량"] * unit_price

        results[menu] = menu_df

    return results



# 전체 보간 실행 로직
def preprocess_all_menus(daily_sales, 
                         unpopular_menus, 
                         new_menus, 
                         common_missing_dates=None):
    results = {}

    # 비인기 메뉴 처리
    for menu in unpopular_menus:
        print(f"[PROCESS-UNPOPULAR] {menu}")
        results[menu] = preprocess_unpopular_menu(daily_sales, menu)

    # 신메뉴 처리
    for menu in new_menus:
        print(f"[PROCESS-NEW] {menu}")
        results[menu] = preprocess_new_menu(daily_sales, menu)

    # 메인 메뉴 처리 (나머지)
    exclude_menus = unpopular_menus + new_menus
    main_results = preprocess_main_menu(
        daily_sales,
        exclude_menus=exclude_menus,
        common_missing_dates=common_missing_dates
    )
    results.update(main_results)

    return results
