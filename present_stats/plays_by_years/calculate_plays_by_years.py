import pandas as pd


def calculate_plays_by_years(df_play_stat: pd.DataFrame) -> pd.DataFrame:
    if len(df_play_stat) == 0:
        return pd.DataFrame()
    # number of new games tried in every year
    df_new_games = df_play_stat.groupby(["name", "objectid"])[["date"]].min()
    df_new_games["year"] = df_new_games["date"].str[0:4].astype(int)
    df_new_games = df_new_games.groupby("year").count()
    df_new_games.rename(columns={"date": "New games tried"}, inplace=True)

    # number of unique games known already at that time
    df_new_games["known_games"] = df_new_games["New games tried"].cumsum()
    df_new_games.rename(columns={"known_games": "Known games"}, inplace=True)

    # number of unique games played in every year
    df_played = df_play_stat
    df_played["year"] = df_played["date"].str[0:4].astype(int)
    df_played = pd.Series(df_played.groupby("year")["objectid"].nunique())
    df_played.rename("Unique games played", inplace=True)

    # number of all plays in every year
    df_all_plays = df_play_stat
    df_all_plays["year"] = df_all_plays["date"].str[0:4].astype(int)
    df_all_plays = df_all_plays.groupby("year")["quantity"].sum()
    df_all_plays.rename("Number of plays", inplace=True)

    df_result = pd.merge(df_new_games, df_played, how="left", on="year")
    df_result = (pd.merge(df_result, df_all_plays, how="left", on="year").sort_values("year", ascending=False).
                 reset_index())
    return df_result
