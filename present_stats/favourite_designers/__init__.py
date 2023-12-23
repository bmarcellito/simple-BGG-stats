import streamlit as st
from present_stats.add_description import add_description

from present_stats.favourite_designers.calculate_favourite_designers import calculate_favourite_designers


def present_favourite_designers() -> None:
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        if "sel_designer" not in st.session_state:
            st.session_state.sel_designer = 'Favourite based on number of games known'
        st.selectbox("How to measure?", ("Favourite based on number of games known", "Favourite based on plays",
                                         "Favourite based on user' ratings"), key='sel_designer')
        col1, col2 = st.columns(2)
        with col1:
            st.toggle(label="Just owned games / all known games", key="toggle_owned")
        with col2:
            st.toggle(label='Include boardgame expansions as well', key="toggle_collection")
        df_favourite_designer = calculate_favourite_designers(st.session_state.my_collection,
                                                              st.session_state.global_game_infodb,
                                                              st.session_state.toggle_owned,
                                                              st.session_state.toggle_collection,
                                                              st.session_state.sel_designer)
        if len(df_favourite_designer) == 0:
            st.write("No data to show :(")
        else:
            st.table(df_favourite_designer)
            add_description("favourite_designers")
    return None
