import streamlit as st

from main_screen_functions.bgg_data_class import BggData
if st.secrets["environment"] == "dev":
    from time import sleep
    import gc
    from sys import getsizeof
    import sys
    from my_logger import log_info, log_error


def extra_admin(my_bgg_data: BggData) -> None:
    if st.secrets["environment"] == "dev":
        ph_admin = st.empty()
        with ph_admin.container():
            # log_info(f'Garbage col: {gc.get_count()}')
            st.write(f'Size of collection: {getsizeof(my_bgg_data.user_collection):,}')
            st.write(f'Size of plays: {getsizeof(my_bgg_data.user_plays):,}')
            st.write(f'Size of game DB: {getsizeof(my_bgg_data.game_info_db):,}')
            st.write(f'Size of play numbers: {getsizeof(my_bgg_data.play_no_db):,}')
            st.write(f'Amount of variables before garbage collection: {gc.get_count()}')
            # gc.collect()
            # st.write(f'Amount of variables after garbage collection: {gc.get_count()}')
            # st.write(st.session_state)
