import pandas as pd
import streamlit as st
import my_gdrive
import my_gdrive.save_functions

from bgg_import.build_item_db.get_items import get_100_items


def create_import_list(df_new_games: pd.DataFrame, df_new_plays: pd.DataFrame, global_game_infodb: pd.DataFrame) \
        -> list:
    if df_new_games.empty and df_new_plays.empty:
        return []
    if not df_new_games.empty:
        possible_new_items = df_new_games.groupby("objectid").count().reset_index()
        possible_new_items_list = possible_new_items["objectid"].tolist()
    else:
        possible_new_items_list = []
    if not df_new_plays.empty:
        possible_new_items = df_new_plays.groupby("objectid").count().reset_index()
        possible_new_items_list = possible_new_items_list + possible_new_items["objectid"].tolist()

    # remove duplicates
    possible_new_items_list = list(set(possible_new_items_list))

    games_to_import_list = []
    if len(global_game_infodb) > 0:
        existing_item_list = global_game_infodb["objectid"].tolist()
        for i in possible_new_items_list:
            if i not in existing_item_list:
                games_to_import_list.append(i)
    else:
        games_to_import_list = possible_new_items_list
    return games_to_import_list


def build_item_db_all(df_new_games: pd.DataFrame, df_new_plays: pd.DataFrame, global_game_infodb: pd.DataFrame,
                      global_play_numdb: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
    sum_error = True
    while sum_error:
        # in rare cases there can be an XML read error and a second parse needed
        # TODO find out why it happens
        games_to_import_list = create_import_list(df_new_games, df_new_plays, global_game_infodb)
        if not games_to_import_list:
            return global_game_infodb, global_play_numdb

        st.caption("STEP 3/3: Importing detailed item information for user's collection...")
        sum_error = False
        chunk = 100
        for i in range((len(games_to_import_list) // chunk)+1):
            import_part = games_to_import_list[i*chunk:(i+1)*chunk]
            placeholder = st.empty()
            with placeholder.container():
                st.caption(f'{len(games_to_import_list)-i*chunk} items left')
                global_game_infodb, global_play_numdb, error = get_100_items(import_part, global_game_infodb,
                                                                             global_play_numdb)
                sum_error = sum_error and error
            placeholder.empty()

    gdrive_processed = st.secrets["gdrive_processed"]
    filename_game_infodb_processed = "game_infoDB"
    filename_playnum_processed = "playnum_infoDB"
    my_gdrive.save_functions.save_background(parent_folder=gdrive_processed, filename=filename_game_infodb_processed,
                                             df=global_game_infodb, concat=["objectid"])
    my_gdrive.save_functions.save_background(parent_folder=gdrive_processed, filename=filename_playnum_processed,
                                             df=global_play_numdb, concat=["objectid", "numplayers"])
    return global_game_infodb, global_play_numdb
