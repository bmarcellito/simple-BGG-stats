import pandas as pd


def calculate_user_and_bgg_ratings(df_collection: pd.DataFrame, df_plays: pd.DataFrame, df_game_infodb: pd.DataFrame,
                                   toggle_owned: bool, toggle_expansion: bool,) -> (pd.DataFrame, int):
    if len(df_collection) == 0:
        return pd.DataFrame(), 0, 0, 0, 0, 0
    df_rating = pd.merge(df_collection, df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    df_rating = pd.DataFrame(df_rating.loc[df_rating["user_rating"] > 0])

    if not toggle_owned:
        df_rating = df_rating.query('own == 1')
    if not toggle_expansion:
        df_rating = df_rating.query('type == "boardgame"')
    if len(df_rating) == 0:
        return pd.DataFrame(), 0, 0, 0, 0, 0

    most_played = pd.DataFrame(df_plays.groupby("objectid").sum())
    df_rating = df_rating.merge(most_played, how="left", left_on="objectid", right_on="index", suffixes=("", "_z"))
    df_rating = df_rating[["name", "numplays", "user_rating", "rating_average"]]
    df_rating.rename(columns={"user_rating": "User's rating", "rating_average": "Average rating on BGG",
                              "numplays": "Number of plays"}, inplace=True)
    df_rating = df_rating.sort_values(by="Number of plays", ascending=False)
    df_rating["color_data"] = "Data"
    min_user_rating = df_rating["User's rating"].min()
    max_user_rating = df_rating["User's rating"].max()+0.2
    min_bgg_rating = df_rating["Average rating on BGG"].min()
    max_bgg_rating = df_rating["Average rating on BGG"].max()+0.2
    min_rating = min(min_user_rating, min_bgg_rating)
    max_rating = max(max_user_rating, max_bgg_rating)

    max_size = int(max(df_rating["Number of plays"].max() // 100, 1))
    if max_size == 1:
        circle_size = max_size*30
    else:
        circle_size = max_size*10
    step = 10
    starting = round(min_rating*10)
    ending = round((max_rating-0.2)*10)
    step_size = (ending-starting) // 10
    for i in range(starting, ending, step_size):
        new_row = pd.DataFrame({"name": "", "Number of plays": 1, "User's rating": i/step,
                                "Average rating on BGG": i/step, "color_data": "Equal values line"},
                               index=[len(df_rating)])
        df_rating = pd.concat([df_rating, new_row])
    return df_rating, circle_size, min_rating, max_rating, min_bgg_rating, max_bgg_rating
