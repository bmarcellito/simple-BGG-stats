import pandas as pd


def calculate_rankings_and_weights(df_game_info: pd.DataFrame, df_collection: pd.DataFrame, df_plays: pd.DataFrame,
                                   h_toggle_owned: bool, h_toggle_expansion: bool) -> \
        (pd.DataFrame, float, float, float, float):
    if (len(df_plays) == 0) or (len(df_collection) == 0):
        return pd.DataFrame(), 0, 0, 0, 0
    most_played = pd.DataFrame(df_plays.groupby("objectid")["quantity"].sum())
    most_played = most_played.sort_values("quantity", ascending=False)
    most_played = most_played.merge(df_game_info, how="left", on="objectid", suffixes=("", "_y"))
    most_played = most_played.merge(df_collection, how="left", on="objectid", suffixes=("", "_y"))
    most_played["year_published"] = most_played["year_published"].clip(1990)

    if not h_toggle_owned:
        most_played = most_played.query('own == 1')
    if not h_toggle_expansion:
        most_played = most_played.query('type == "boardgame"')
    if len(most_played) == 0:
        return pd.DataFrame(), 0, 0, 0, 0

    most_played = most_played[["objectid", "type", "name", "year_published", "weight", "quantity", "rating_average"]]
    most_played = most_played.sort_values("quantity", ascending=False)
    most_played.rename(columns={"rating_average": "Average rating on BGG", "weight": "Weight",
                                "quantity": "Number of plays"}, inplace=True)

    min_weight = most_played["Weight"].min()
    max_weight = most_played["Weight"].max()+0.2
    min_bgg_rating = most_played["Average rating on BGG"].min()
    max_bgg_rating = most_played["Average rating on BGG"].max()+0.2

    return most_played, min_weight, max_weight, min_bgg_rating, max_bgg_rating
