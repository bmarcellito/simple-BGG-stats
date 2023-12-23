import pandas as pd


def calculate_basics(bgg_username: str, df_collection: pd.DataFrame, df_plays: pd.DataFrame, df_game_info: pd.DataFrame,
                     df_user_cache: pd.DataFrame) -> (pd.DataFrame, str):
    df_game_info_fresh = df_game_info.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True)
    if len(df_collection) == 0:
        collection_all = 0
        collection_games = 0
        collection_exp = 0
        owned_all = 0
        owned_games = 0
        owned_exp = 0
        rated_all = 0
        rated_games = 0
        rated_exp = 0
        more_all = 0
        more_games = 0
        more_exp = 0
        plays_mean = 0
        plays_median = 0
    else:
        collection_merged = pd.merge(df_collection, df_game_info_fresh, how="left", on="objectid")
        collection_all = len(collection_merged)
        collection_games = len(collection_merged.query('type == "boardgame"'))
        collection_exp = len(collection_merged.query('type == "boardgameexpansion"'))
        owned_all = df_collection["own"].loc[df_collection["own"] == 1].count()
        owned_games = len(collection_merged.query('(type == "boardgame") and (own == 1)'))
        owned_exp = len(collection_merged.query('(type == "boardgameexpansion") and (own == 1)'))
        rated_all = len(collection_merged.query('user_rating > 0'))
        rated_games = len(collection_merged.query('(type == "boardgame") and (user_rating > 0)'))
        rated_exp = len(collection_merged.query('(type == "boardgameexpansion") and (user_rating > 0)'))
        more_all = df_collection["numplays"].loc[df_collection["numplays"] > 1].count()
        more_games = len(collection_merged.query('(type == "boardgame") and (numplays > 1)'))
        more_exp = len(collection_merged.query('(type == "boardgameexpansion") and (numplays > 1)'))
        plays_mean = df_collection["numplays"].mean()
        plays_median = df_collection["numplays"].median()

    if len(df_plays) == 0:
        plays_all = 0
        plays_games = 0
        plays_exp = 0
        tried_all = 0
        tried_games = 0
        tried_exp = 0
        first_play = "-"
    else:
        plays_merged = pd.merge(df_plays, df_game_info_fresh, how="left", on="objectid")
        plays_all = df_plays["quantity"].sum()
        plays_games = plays_merged.query('type == "boardgame"')
        plays_games = plays_games["quantity"].sum()
        plays_exp = plays_merged.query('type == "boardgameexpansion"')
        plays_exp = plays_exp["quantity"].sum()
        tried_all = df_plays["objectid"].nunique()
        tried_games = plays_merged.query('type == "boardgame"')
        tried_games = tried_games["objectid"].nunique()
        tried_exp = plays_merged.query('type == "boardgameexpansion"')
        tried_exp = tried_exp["objectid"].nunique()
        first_play = df_plays.date.min()

    data = {"Name": ["Size of BGG collection", "Number of items owned", "Number of recorded plays",
                     "Number of unique items tried", "Played more than once",
                     "Number of items rated by the user"],
            "Games": [collection_games, owned_games, plays_games, tried_games, more_games, rated_games],
            "Expansions": [collection_exp, owned_exp, plays_exp, tried_exp, more_exp, rated_exp],
            "All": [collection_all, owned_all, plays_all, tried_all, more_all, rated_all]}
    df_basic = pd.DataFrame(data, index=pd.RangeIndex(start=1, stop=7, step=1))

    user_info = df_user_cache.query(f'username == "{bgg_username}"').reset_index()
    first_name = user_info.loc[0, "first_name"]
    last_name = user_info.loc[0, "last_name"]
    if len(first_name+last_name) > 0:
        row_name = f'Name: {first_name} {last_name}  \n'
    else:
        row_name = f'Name: not specified  \n'
    df_text = (f'{row_name}'
               f'First play recorded on: {first_play}  \n'
               f'Mean of plays with a specific game: {plays_mean:.2f}  \n'
               f'Median of plays with a specific game: {plays_median:.2f}')
    return df_basic, df_text
