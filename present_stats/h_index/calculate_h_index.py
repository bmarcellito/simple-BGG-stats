from datetime import datetime
import pandas as pd


def count_h_without_names(df_raw: pd.DataFrame) -> int:
    if df_raw.empty:
        return 0
    df_count = df_raw.groupby("Name", sort=False).sum().reset_index()
    df_count = df_count.sort_values(by=["Number of plays", "Name"], ascending=[False, True]).reset_index()
    i = 0
    while True:
        try:
            if df_count.iloc[i]["Number of plays"] < i + 1:
                break
        except IndexError:
            break
        i += 1

    return i


def count_h_with_names(df_raw: pd.DataFrame) -> (pd.DataFrame, int):
    if df_raw.empty:
        return df_raw, 0
    df_count = df_raw.groupby("Name", sort=False).sum().reset_index()
    df_count = df_count.sort_values(by=["Number of plays", "Name"], ascending=[False, True]).reset_index()
    i = 0
    while True:
        try:
            if df_count.iloc[i]["Number of plays"] < i + 1:
                break
        except IndexError:
            break
        i += 1

    df_h_index = pd.DataFrame(df_count[["Name", "Number of plays"]].loc[df_count["Number of plays"] >= i])
    if len(df_h_index) > i:
        extra_text = "Also in the H-index range are: "
        for index in range(i, len(df_h_index)):
            extra_text = (f'{extra_text}{df_h_index.at[index, "Name"]} '
                          f'({df_h_index.at[index, "Number of plays"]} plays), ')
        extra_text = extra_text[:-2]
        df_h_index.at[i, "Name"] = extra_text
        df_h_index["Number of plays"] = df_h_index["Number of plays"].astype(str)
        df_h_index.at[i, "Number of plays"] = f'At least {i}'
        cut = i + 1
    else:
        cut = i
    df_h_index.index = pd.RangeIndex(start=1, stop=len(df_h_index) + 1, step=1)
    return df_h_index.head(cut), i


def prepare_db(df_plays: pd.DataFrame, df_game_infodb: pd.DataFrame, toggle_expansion: bool) -> pd.DataFrame:
    df_game_infodb_fresh = df_game_infodb.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True)
    df = pd.merge(df_plays, df_game_infodb_fresh, how="left", on="objectid", suffixes=("", "_y"))
    if not toggle_expansion:
        df = df.query('type == "boardgame"')
    if len(df) == 0:
        return pd.DataFrame()
    df = df[["name", "quantity", "date"]]
    df.rename(columns={"name": "Name", "quantity": "Number of plays", "date": "Date"}, inplace=True)
    df = df.reset_index()
    return df


def calculate_h_index(df_plays: pd.DataFrame, df_game_infodb: pd.DataFrame, toggle_expansion: bool, stat_type: str) \
        -> list:
    if len(df_plays) == 0:
        return []
    df_game_infodb_fresh = df_game_infodb.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True)
    df = pd.merge(df_plays, df_game_infodb_fresh, how="left", on="objectid", suffixes=("", "_y"))
    if not toggle_expansion:
        df = df.query('type == "boardgame"')
    if len(df) == 0:
        return []
    df = df[["name", "quantity", "date"]]
    df.rename(columns={"name": "Name", "quantity": "Number of plays", "date": "Date"}, inplace=True)
    df = df.reset_index()

    match stat_type:
        case 'All times':
            df_result, i = count_h_with_names(df)
            result = [[i, df_result, ""]]
        case 'For each calendar year':
            df["Date"] = df["Date"].str[0:4].astype(int)
            df = df.sort_values("Date").reset_index(drop=True)
            plays_years = df["Date"].unique().tolist()
            no_row = len(plays_years)
            result = []
            for index in range(no_row):
                df_yearly = df.query(f'Date == {plays_years[index]}')
                df_result, i = count_h_with_names(df_yearly)
                result.append([i, df_result, plays_years[index]])
        case _:
            result = []
    return result


def calculate_h_index_graph(df_plays: pd.DataFrame, df_game_infodb: pd.DataFrame, toggle_expansion: bool) -> (
        pd.DataFrame):
    if len(df_plays) == 0:
        return pd.DataFrame()
    df = prepare_db(df_plays, df_game_infodb, toggle_expansion)

    df["Date"] = df["Date"].str[0:7]
    start = df["Date"].min()
    start_year = start[0:4]
    start_month = start[5:7]
    end_year = str(datetime.today().year)
    end_month = str(datetime.today().month).zfill(2)
    if end_month == "12":
        end_month = "01"
        end_year = str(int(end_year) + 1)
    else:
        end_month = str(int(end_month) + 1).zfill(2)

    result = pd.DataFrame(columns=["Period", "All times", "12-month-window"])
    while True:
        max_date = f'{start_year}-{start_month}'
        df_period = df.query(f'Date <= "{max_date}"')
        i = count_h_without_names(df_period)
        min_year = str(int(start_year)-1)
        min_date = f'{min_year}-{start_month}'
        df_period = df_period.query(f'Date > "{min_date}"')
        j = count_h_without_names(df_period)
        next_line = {"Period": [max_date], "All times": [i], "12-month-window": [j]}
        result = pd.concat([result, pd.DataFrame(next_line)])
        if start_month == "12":
            start_month = "01"
            start_year = str(int(start_year)+1)
        else:
            start_month = str(int(start_month)+1).zfill(2)
        if (start_year == end_year) and (start_month == end_month):
            break
    return result
