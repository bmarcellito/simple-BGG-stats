import pandas as pd
from my_logger import log_error


def calculate_games_by_weight(df_game_info: pd.DataFrame, df_collection: pd.DataFrame, df_plays: pd.DataFrame,
                              toggle_owned: bool, toggle_expansion: bool) -> pd.DataFrame:
    if (len(df_plays) == 0) or (len(df_collection) == 0):
        return pd.DataFrame()
    if not df_collection.empty:
        possible_new_items = df_collection.groupby("objectid").count().reset_index()
        item_list = possible_new_items["objectid"].tolist()
    else:
        item_list = []
    if len(df_plays) != 0:
        possible_new_items = df_plays.groupby("objectid").count().reset_index()
        item_list = item_list + possible_new_items["objectid"].tolist()
    # remove duplicates
    item_list = list(set(item_list))

    weight_list = df_game_info.query(f'objectid in {item_list}')
    weight_list = weight_list.merge(df_collection, how="left", on="objectid", suffixes=("", "_y"))
    if not toggle_owned:
        weight_list = weight_list.query('own == 1')
    if not toggle_expansion:
        weight_list = weight_list.query('type == "boardgame"')

    if len(weight_list) == 0:
        return pd.DataFrame()
    weight_list = weight_list.reset_index()

    weight_list.loc["Number of plays"] = 0
    df_grouped_plays = df_plays.groupby("objectid")[["quantity"]].sum()
    df_grouped_plays.dropna(inplace=True)
    for i in range(len(weight_list)-1):
        object_id = weight_list.at[i, "objectid"]
        try:
            weight_list.loc[i, "Number of plays"] = df_grouped_plays.loc[object_id, "quantity"]
        except KeyError:
            weight_list.loc[i, "Number of plays"] = 0
        except ValueError as err:
            log_error(f'calculate_games_by_weight - {err}')

    bucket = 1
    bucket_size = 0.5
    weight_graph = pd.DataFrame(columns=["Weight", "Known games", "Played games"])
    while True:
        row_no = len(weight_graph)
        weight_graph.loc[row_no] = [bucket, 0, 0]
        for i in range(len(weight_list)-1):
            if bucket >= weight_list.at[i, "weight"] > bucket-bucket_size:
                weight_graph.at[row_no, "Known games"] += 1
                weight_graph.at[row_no, "Played games"] += weight_list.at[i, "Number of plays"]
        if bucket >= 5:
            break
        bucket += bucket_size
    return weight_graph
