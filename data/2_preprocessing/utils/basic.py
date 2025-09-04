# 컬럼을 수치형으로 변환
def int_format(df, col):
    df[col] = df[col].astype(str)
    df[col] = df[col].str.replace(',', '')
    df[col] = pd.to_numeric(df[col], errors="coerce")
    return df[col]

# 기간 절삭
def trim_to_yesterday(df, datetime_col="판매일시"):
    """
    DataFrame에서 지정된 datetime 컬럼을 기준으로 전날 23:59:59까지 데이터만 필터링
    """
    cutoff = (pd.Timestamp.today().normalize() - pd.Timedelta(days=1)) \
             + pd.Timedelta(hours=23, minutes=59, seconds=59)

    return df[df[datetime_col] <= cutoff]