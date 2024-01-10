import streamlit as st
from datetime import datetime, timedelta, timezone

from main_screen_functions.bgg_data_class import BggData
from bgg_import.build_item_db import build_item_db_all
from bgg_import.get_user_collection import import_user_collection, get_user_collection
from bgg_import.get_user_plays import import_user_plays, get_user_plays
from bgg_import.get_functions import (get_game_infodb, get_play_no_db, get_username_cache)
from bgg_import.check_user import refresh_last_checked, get_user_last_checked


def import_user_data(username: str, user_folder_id: str, refresh: int) -> BggData:
    def age_of_cached_data() -> int:
        time_of_creation = str(get_user_last_checked(username))
        time = datetime.strptime(time_of_creation, "%Y-%m-%d, %H:%M:%S")
        age = datetime.now() - time
        age_in_days = age.days
        return age_in_days

    st.caption('Based on the size of the collection, importing can take couple of minutes!    \nPlease be patient!')

    st.caption(f'STEP 1/3: Importing collection of {username}...')
    my_user_collection = get_user_collection(username, user_folder_id)
    if refresh == 0:
        fresh_user_collection = import_user_collection(username, user_folder_id, 0)
        my_user_collection.status = fresh_user_collection.status
        my_user_collection.data = fresh_user_collection.data
        my_user_collection.import_msg = fresh_user_collection.import_msg
        refresh_last_checked(username)
        del fresh_user_collection
    if my_user_collection.status:
        how_fresh = age_of_cached_data()
        st.caption(f'{my_user_collection.import_msg} It is {how_fresh} days old.')
    else:
        st.caption(my_user_collection.import_msg)
        return BggData()

    st.caption(f'STEP 2/3: Importing plays of {username}...')
    my_plays = get_user_plays(username, user_folder_id)
    if refresh == 0:
        fresh_user_plays = import_user_plays(username, user_folder_id, 0)
        my_plays.status = fresh_user_plays.status
        my_plays.data = fresh_user_plays.data
        my_plays.import_msg = fresh_user_plays.import_msg
        del fresh_user_plays
    st.caption(my_plays.import_msg)

    df_game_infodb = get_game_infodb()
    df_play_no_db = get_play_no_db()
    # TODO should collect return value???
    df_game_infodb.data, df_play_no_db.data = build_item_db_all(my_user_collection.data, my_plays.data,
                                                                df_game_infodb.data, df_play_no_db.data)
    username_cache = get_username_cache()
    my_bgg_data = BggData()
    my_bgg_data.status = True
    my_bgg_data.user_collection = my_user_collection.data
    my_bgg_data.user_plays = my_plays.data
    my_bgg_data.game_info_db = df_game_infodb.data
    my_bgg_data.play_no_db = df_play_no_db.data
    my_bgg_data.username_cache = username_cache.data
    del my_user_collection
    del my_plays
    del df_game_infodb
    del df_play_no_db
    return my_bgg_data
