import streamlit as st

from main_screen_functions.bgg_data_class import BggData
from present_stats.basics import present_basics
from present_stats.collection import present_collection
from present_stats.h_index import present_h_index
from present_stats.favourite_designers import present_favourite_designers
from present_stats.by_publication_year import present_by_publication_year
from present_stats.games_by_weight import present_games_by_weight
from present_stats.plays_by_years import present_plays_by_years
from present_stats.bgg_toplist import present_bgg_toplist
from present_stats.rankings_and_weights import present_rankings_and_weights
from present_stats.user_and_bgg_ratings import present_user_and_bgg_ratings
from present_stats.add_description import add_description
from main_screen_functions.presentation_hack import clear_ph_element


def set_state(selectbox_name: str) -> None:
    if selectbox_name not in st.session_state:
        st.session_state[selectbox_name] = 'Basic statistics'
    if "previous_user" not in st.session_state:
        st.session_state.previous_user = st.session_state.bgg_username
    if st.session_state.previous_user != st.session_state.bgg_username:
        previous_name = f'stat_key_{st.session_state.previous_user}'
        del st.session_state[previous_name]
    st.session_state.previous_user = st.session_state.bgg_username


def present_stat_selector(my_bgg_data: BggData) -> None:
    def different_stat_selected() -> None:
        clear_ph_element([ph_stat])

    select_options = ['Basic statistics',
                      'User collection',
                      'Favourite designers',
                      'H-index',
                      'Games and plays by publication years',
                      'Weight distribution of user\'s games and plays',
                      'Play statistics by year',
                      'Games known from BGG top list',
                      'Stat around game weight',
                      'Stat around ratings']

    st.title(f'Statistics of {st.session_state.bgg_username}')
    ph_selector = st.empty()
    ph_stat = st.empty()
    selectbox_name = f'stat_key_{st.session_state.bgg_username}'
    set_state(selectbox_name)

    with ph_selector.container():
        st.selectbox(label="Choose a statistic", options=select_options, key=selectbox_name,
                     on_change=different_stat_selected)

    with ph_stat.container():
        match st.session_state[selectbox_name]:
            case "Basic statistics": present_basics(my_bgg_data)
            case "User collection": present_collection(my_bgg_data)
            case "Favourite designers": present_favourite_designers(my_bgg_data)
            case "H-index": present_h_index(my_bgg_data)
            case "Games and plays by publication years": present_by_publication_year(my_bgg_data)
            case "Weight distribution of user's games and plays": present_games_by_weight(my_bgg_data)
            case "Play statistics by year": present_plays_by_years(my_bgg_data)
            case "Games known from BGG top list": present_bgg_toplist(my_bgg_data)
            case "Stat around game weight": present_rankings_and_weights(my_bgg_data)
            case "Stat around ratings": present_user_and_bgg_ratings(my_bgg_data)
    return None
