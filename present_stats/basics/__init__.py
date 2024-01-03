import streamlit as st

from present_stats.add_description import add_description
from present_stats.basics.calculate_basics import calculate_basics
from bgg_import.get_functions import get_game_infodb, get_username_cache


def present_basics():
    with st.spinner('Please wait, calculating statistics...'):
        df_game_infodb = get_game_infodb()
        df_username_cache = get_username_cache()
        df_basic, text_basic = calculate_basics(st.session_state.bgg_username, st.session_state.my_collection,
                                                st.session_state.my_plays, df_game_infodb, df_username_cache)
    st.write(text_basic)
    st.dataframe(df_basic, use_container_width=True)
    add_description("basics")
    del df_game_infodb
    del df_username_cache
    return None
