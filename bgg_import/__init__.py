import streamlit as st

from main_screen_functions.bgg_data_class import BggData
from bgg_import.build_item_db import build_item_db_all
from bgg_import.get_user_collection import user_collection
from bgg_import.get_user_plays import user_plays
from bgg_import.get_functions import (get_game_infodb, get_play_no_db, get_user_collection, get_user_plays,
                                      get_username_cache)


def import_user_data(username: str, refresh: int) -> BggData:
    st.caption('Based on the size of the collection, importing can take couple of minutes!    \nPlease be patient!')

    st.caption(f'STEP 1/3: Importing collection of {username}...')
    my_user_collection = get_user_collection(username)
    if refresh == 0:
        df_collection, import_text = user_collection(username, 0)
        my_user_collection.data = df_collection
        my_user_collection.import_text = import_text
        del df_collection
        del import_text
    st.caption(my_user_collection.import_text)

    st.caption(f'STEP 2/3: Importing plays of {username}...')
    my_plays = get_user_plays(username)
    if refresh == 0:
        df_user_plays, feedback_play = user_plays(username, 0)
        my_plays.data = df_user_plays
        my_plays.import_text = feedback_play
        del df_user_plays
        del feedback_play
    st.caption(my_plays.import_text)

    df_game_infodb = get_game_infodb()
    df_play_no_db = get_play_no_db()
    # TODO should collect return value???
    df_game_infodb.data, df_play_no_db.data = build_item_db_all(my_user_collection.data, my_plays.data,
                                                                df_game_infodb.data, df_play_no_db.data)
    my_bgg_data = BggData()
    my_bgg_data.user_collection = my_user_collection.data
    my_bgg_data.user_plays = my_plays.data
    my_bgg_data.game_info_db = df_game_infodb.data
    my_bgg_data.play_no_db = df_play_no_db.data
    del my_user_collection
    del my_plays
    del df_game_infodb
    del df_play_no_db
    return my_bgg_data
