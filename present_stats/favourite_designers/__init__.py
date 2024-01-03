import streamlit as st

from present_stats.favourite_designers.calculate_favourite_designers import calculate_favourite_designers
from present_stats.add_description import add_description
from bgg_import.get_functions import get_game_infodb


def present_favourite_designers() -> None:
    if "sel_designer" not in st.session_state:
        st.session_state.sel_designer = 'Favourite based on number of games known'
    st.selectbox("How to measure?", ("Favourite based on number of games known", "Favourite based on plays",
                                     "Favourite based on user' ratings"), key='sel_designer')
    col1, col2 = st.columns(2)
    with col1:
        st.toggle(label="Just owned games / all known games", key="toggle_owned")
    with col2:
        st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")

    with st.spinner('Please wait, calculating statistics...'):
        df_game_infodb = get_game_infodb()
        df_favourite_designer = calculate_favourite_designers(st.session_state.my_collection,
                                                              df_game_infodb,
                                                              st.session_state.toggle_owned,
                                                              st.session_state.toggle_expansion,
                                                              st.session_state.sel_designer)
    if len(df_favourite_designer) == 0:
        st.write("No data to show :(")
    else:
        # st.markdown("""
        # <style>
        # td {vertical-align: top;}
        # </style>
        # """, unsafe_allow_html=True)
        st.table(df_favourite_designer)
        add_description("favourite_designers")
    del df_game_infodb
    return None
