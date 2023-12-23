import streamlit as st
from present_stats.add_description import add_description

from present_stats.basics.calculate_basics import calculate_basics


def present_basics():
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        df_basic, text_basic = calculate_basics(st.session_state.bgg_username, st.session_state.my_collection,
                                                st.session_state.my_plays, st.session_state.global_game_infodb,
                                                st.session_state.check_user_cache)
        st.dataframe(df_basic, use_container_width=True)
        st.write(text_basic)
        add_description("basics")
    return None
