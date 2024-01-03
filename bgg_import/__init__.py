import streamlit as st

from bgg_import.build_item_db import build_item_db_all
from bgg_import.get_user_collection import user_collection
from bgg_import.get_user_plays import user_plays
from bgg_import.get_functions import get_game_infodb, get_play_no_db
from my_logger import timeit


@timeit
def import_user_data(username: str, refresh: int) -> None:
    st.caption('Based on the size of the collection, importing can take couple of minutes!    \nPlease be patient!')
    if refresh == 0:
        user_collection.clear()
        user_plays.clear()
    st.session_state.my_collection = user_collection(username, refresh)
    st.session_state.my_plays = user_plays(username, refresh)
    df_game_infodb = get_game_infodb()
    df_play_no_db = get_play_no_db()
    # TODO should collect return value???
    build_item_db_all(st.session_state.my_collection, st.session_state.my_plays, df_game_infodb, df_play_no_db)
