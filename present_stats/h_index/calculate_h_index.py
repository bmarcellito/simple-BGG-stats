from datetime import datetime, timedelta
import pandas as pd


def count_h(df_raw: pd.DataFrame) -> (pd.DataFrame, int):
    if df_raw.empty:
        return df_raw, 0
    df_count = df_raw.groupby("Name", sort=False).sum().reset_index()
    df_count = df_count.sort_values(by=["Number of plays", "Name"], ascending=[False, True]).reset_index()
    i = 0
    while 0 == 0:
        try:
            if df_count.iloc[i]["Number of plays"] < i + 1:
                break
        except IndexError:
            break
        i += 1

    df_player_num_votes = pd.DataFrame(df_count[["Name", "Number of plays"]].loc[df_count["Number of plays"] >= i])
    if len(df_player_num_votes) > i:
        extra_text = "Also in the H-index range are: "
        for index in range(i, len(df_player_num_votes)):
            extra_text = (f'{extra_text}{df_player_num_votes.at[index, "Name"]} '
                          f'({df_player_num_votes.at[index, "Number of plays"]} plays), ')
        extra_text = extra_text[:-2]
        df_player_num_votes.at[i, "Name"] = extra_text
        df_player_num_votes["Number of plays"] = df_player_num_votes["Number of plays"].astype(str)
        df_player_num_votes.at[i, "Number of plays"] = f'At least {i}'
        cut = i + 1
    else:
        cut = i
    df_player_num_votes.index = pd.RangeIndex(start=1, stop=len(df_player_num_votes) + 1, step=1)
    return df_player_num_votes.head(cut), i


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
            df_result, i = count_h(df)
            result = [[i, df_result, ""]]
        case 'Last year (starting from today)':
            no_row = len(df)
            one_years_ago = datetime.today() - timedelta(days=365)
            for index in range(no_row):
                play_date = datetime.strptime(df.at[index, "Date"], "%Y-%m-%d")
                if play_date > one_years_ago:
                    df.at[index, "Date"] = 1
                else:
                    df.at[index, "Date"] = 0
            df = df.query(f'Date == 1')
            df_result, i = count_h(df)
            result = [[i, df_result, ""]]
        case 'For each calendar year':
            df["Date"] = df["Date"].str[0:4].astype(int)
            df = df.sort_values("Date").reset_index(drop=True)
            plays_years = df["Date"].unique().tolist()
            no_row = len(plays_years)
            result = []
            for index in range(no_row):
                df_yearly = df.query(f'Date == {plays_years[index]}')
                df_result, i = count_h(df_yearly)
                result.append([i, df_result, plays_years[index]])
        case _:
            result = []
    return result
