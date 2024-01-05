import streamlit as st

from main_screen_functions.bgg_data_class import BggData
from present_stats.favourite_designers.calculate_favourite_designers import calculate_favourite_designers
from present_stats.add_description import add_description


def present_favourite_designers(my_data_bgg: BggData) -> None:
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
        df_favourite_designer = calculate_favourite_designers(my_data_bgg.user_collection,
                                                              my_data_bgg.game_info_db,
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
    return None
