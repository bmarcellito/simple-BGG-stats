import streamlit as st

from main_screen_functions.bgg_data_class import BggData
from present_stats.add_description import add_description
from present_stats.basics.calculate_basics import calculate_basics
from present_stats.basics.calculate_basics_plays import calculate_basics_plays


def present_basics(my_bgg_data: BggData):
    with st.spinner('Please wait, calculating statistics...'):
        df_basic, text_basic = calculate_basics(st.session_state.bgg_username, my_bgg_data.user_collection,
                                                my_bgg_data.user_plays, my_bgg_data.game_info_db,
                                                my_bgg_data.username_cache)
    st.write(text_basic)
    st.dataframe(df_basic, use_container_width=True)
    st.subheader("Monthly play number")
    st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")
    with st.spinner('Please wait, calculating statistics...'):
        df_plays = calculate_basics_plays(my_bgg_data.user_plays, my_bgg_data.game_info_db,
                                          st.session_state.toggle_expansion)
    if df_plays.empty:
        st.write("No data to show :(")
    else:
        st.line_chart(df_plays, x="Period", y=["Monthly plays", "Averaged monthly plays"], height=400)
    add_description("basics")
    return None
