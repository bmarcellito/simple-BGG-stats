import string

import pandas as pd


def calculate_user_and_bgg_ratings(df_collection: pd.DataFrame, df_plays: pd.DataFrame, df_game_infodb: pd.DataFrame,
                                   toggle_owned: bool, toggle_collection: bool,) -> (pd.DataFrame, int):
    if len(df_collection) == 0:
        return pd.DataFrame(), 0
    df_rating = pd.merge(df_collection, df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    df_rating = pd.DataFrame(df_rating.loc[df_rating["user_rating"] > 0])

    if not toggle_owned:
        df_rating = df_rating.query('own == 1')
    if not toggle_collection:
        df_rating = df_rating.query('type == "boardgame"')
    if len(df_rating) == 0:
        return pd.DataFrame(), 0

    most_played = pd.DataFrame(df_plays.groupby("objectid").sum())
    df_rating = df_rating.merge(most_played, how="left", left_on="objectid", right_on="index", suffixes=("", "_z"))
    df_rating = df_rating[["name", "numplays", "user_rating", "rating_average"]]
    df_rating.rename(columns={"user_rating": "User's rating", "rating_average": "Average rating on BGG",
                              "numplays": "Number of plays"}, inplace=True)
    df_rating = df_rating.sort_values(by="Number of plays", ascending=False)
    df_rating["color_data"] = "Data"

    max_size = int(max(df_rating["Number of plays"].max() // 100, 1))
    if max_size == 1:
        circle_size = max_size*10
    else:
        circle_size = max_size*4
    step = max_size*5
    for i in range(step*10):
        new_row = pd.DataFrame({"name": "", "Number of plays": max_size, "User's rating": i/step,
                                "Average rating on BGG": i/step, "color_data": "Equal values line"},
                               index=[len(df_rating)])
        df_rating = pd.concat([df_rating, new_row])
    return df_rating, circle_size
