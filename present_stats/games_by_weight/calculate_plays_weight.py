import pandas as pd
from datetime import datetime


def calculate_plays_weight(df_plays: pd.DataFrame, df_game_infodb: pd.DataFrame, toggle_expansion: bool) -> (
        pd.DataFrame):
    if len(df_plays) == 0:
        return pd.DataFrame()
    df_game_infodb_fresh = df_game_infodb.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True)
    df = pd.merge(df_plays, df_game_infodb_fresh, how="left", on="objectid", suffixes=("", "_y"))
    if not toggle_expansion:
        df = df.query('type == "boardgame"')

    df["date"] = df["date"].str[0:7]
    start = df["date"].min()
    start_year = start[0:4]
    start_month = start[5:7]
    end_year = str(datetime.today().year)
    end_month = str(datetime.today().month).zfill(2)
    if end_month == "12":
        end_month = "01"
        end_year = str(int(end_year) + 1)
    else:
        end_month = str(int(end_month) + 1).zfill(2)

    df_result = df[["date", "quantity", "weight"]]
    df_result = df_result.groupby("date").sum().reset_index()
    for row in range(len(df_result)):
        df_result.loc[row, "weight"] = df_result.loc[row, "weight"] / df_result.loc[row, "quantity"]
    while True:
        date_to_check = f'{start_year}-{start_month}'
        if date_to_check not in df_result["date"].values:
            next_line = {"date": [date_to_check]}
            df_result = pd.concat([df_result, pd.DataFrame(next_line)])
        if start_month == "12":
            start_month = "01"
            start_year = str(int(start_year)+1)
        else:
            start_month = str(int(start_month)+1).zfill(2)
        if (start_year == end_year) and (start_month == end_month):
            break
    df_result = df_result.sort_values(by=["date"]).reset_index()
    df_window = df_result["weight"].rolling(window=12, min_periods=1).mean()
    df_result.columns = ["index", "Date", "quantity", "Weight"]
    df_result = pd.concat([df_result, df_window], axis=1)
    df_result.columns = ["index", "Date", "quantity", "Average weight of monthly plays", "Rolling window average"]
    df_result = df_result[["Date", "Average weight of monthly plays", "Rolling window average"]]
    return df_result
