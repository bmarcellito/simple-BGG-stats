import streamlit as st
from present_stats.add_description import add_description

from present_stats.basics.calculate_basics import calculate_basics


def present_basics():
    with st.spinner('Please wait, calculating statistics...'):
        df_basic, text_basic = calculate_basics(st.session_state.bgg_username, st.session_state.my_collection,
                                                st.session_state.my_plays, st.session_state.global_game_infodb,
                                                st.session_state.check_user_cache)
    st.write(text_basic)
    st.dataframe(df_basic, use_container_width=True)
    add_description("basics")
    return None
