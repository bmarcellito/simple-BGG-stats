import pandas as pd


def calculate_ideal_player_number(df_updated_collection: pd.DataFrame, df_playnum_infodb: pd.DataFrame):
    row_no = len(df_updated_collection)
    for index in range(row_no):
        feedback = [0, 0, 0, 0, 0, 0, 0, 0]
        object_id = int(df_updated_collection.at[index, "objectid"])
        try:
            min_player = int(df_updated_collection.at[index, "min_player"])
        except ValueError:
            min_player = 0
        try:
            max_player = min(int(df_updated_collection.at[index, "max_player"]), 8)
        except ValueError:
            max_player = 0
        player_info = df_playnum_infodb.query(f'objectid == {object_id}').reset_index()
        inner_row_no = len(player_info)
        if inner_row_no == 0:
            df_updated_collection.at[index, "objectid"] = 0
            df_updated_collection.at[index, "own"] = feedback
            continue
        for j in range(inner_row_no):
            current_playernum = int(player_info.at[j, "numplayers"])
            if min_player <= current_playernum <= max_player:
                best = int(player_info.at[j, "best"])
                rec = int(player_info.at[j, "recommended"] * 1)
                not_rec = int(player_info.at[j, "not recommended"])
                feedback[current_playernum - 1] = best * 3 + rec + not_rec * 0
            else:
                continue
        votes = sum(feedback)
        if votes > 0:
            for k in range(8):
                feedback[k] = (feedback[k] * 100) // votes
        df_updated_collection.at[index, "objectid"] = feedback.index(max(feedback)) + 1
        df_updated_collection.at[index, "own"] = feedback


def calculate_collection(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame, df_playnum_infodb: pd.DataFrame,
                         toggle_owned: bool, toggle_expansion: bool, player_range: (int, int)) -> pd.DataFrame:
    if len(df_collection) == 0:
        return pd.DataFrame()
    df_ordered_collection = df_collection.sort_values("name").reset_index(drop=True)
    df_updated_collection = df_ordered_collection.merge(df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    df_updated_collection.drop_duplicates(subset=["objectid"], keep="last", inplace=True, ignore_index=True)

    if not toggle_owned:
        df_updated_collection = df_updated_collection.query('own == 1')
    if not toggle_expansion:
        df_updated_collection = df_updated_collection.query('type == "boardgame"')
    if len(df_updated_collection) == 0:
        return pd.DataFrame()
    df_updated_collection.reset_index(drop=True, inplace=True)
    df_updated_collection = df_updated_collection[["name", "numplays", "user_rating", "weight",
                                                   "min_player", "max_player", "objectid",
                                                   "own", "image", "thumbnail"]]
    df_updated_collection["own"] = df_updated_collection["own"].astype(object)

    # create link for the items
    df_updated_collection = pd.DataFrame(df_updated_collection.rename(columns={"thumbnail": "Link"}))
    pos_link = df_updated_collection.columns.get_loc("Link")
    pos_objectid = df_updated_collection.columns.get_loc("objectid")
    for i in range(len(df_updated_collection)):
        df_updated_collection.iloc[i, pos_link] = \
            f'https://boardgamegeek.com/boardgame/{df_updated_collection.iloc[i, pos_objectid]}'

    calculate_ideal_player_number(df_updated_collection, df_playnum_infodb)

    df_updated_collection["objectid"] = df_updated_collection["objectid"].astype(int)
    df_updated_collection = df_updated_collection.query(f'objectid >= {player_range[0]}')
    df_updated_collection = df_updated_collection.query(f'objectid <= {player_range[1]}')

    df_updated_collection.columns = ["Name", "No plays", "User\'s rating", "Weight", "Min player", "Max player",
                                     "Ideal player no", "BGG votes on player numbers", "Image", "Link"]
    return df_updated_collection
