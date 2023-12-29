from time import sleep
import streamlit as st

from bgg_import.build_item_db import build_item_db_all
from bgg_import.get_user_collection import user_collection
from bgg_import.get_user_plays import user_plays
from my_logger import timeit


@timeit
def import_user_data(username: str, refresh: int) -> None:
    st.caption('Based on the size of the collection, importing can take couple of minutes!    \nPlease be patient!')
    st.session_state.my_collection = user_collection(username, refresh)
    st.session_state.my_plays = user_plays(username, refresh)
    while ("global_game_infodb" not in st.session_state) or ("global_play_numdb" not in st.session_state):
        # still loading - has to wait a bit
        sleep(1)
    st.session_state.global_game_infodb, st.session_state.global_play_numdb = build_item_db_all(
        st.session_state.my_collection, st.session_state.my_plays, st.session_state.global_game_infodb,
        st.session_state.global_play_numdb)
