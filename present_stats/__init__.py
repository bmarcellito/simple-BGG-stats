import streamlit as st

from present_stats.basics import present_basics
from present_stats.collection import present_collection
from present_stats.h_index import present_h_index
from present_stats.favourite_designers import present_favourite_designers
from present_stats.games_by_publication_year import present_games_by_publication_year
from present_stats.age_of_games_played import present_age_of_games_played
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
    if st.session_state.user_state == "User_imported_now":
        if "previous_user" in st.session_state:
            previous_name = f'stat_key_{st.session_state.previous_user}'
            del st.session_state[previous_name]
        st.session_state.user_state = "User_imported"
    st.session_state.previous_user = st.session_state.bgg_username


def present_stat_selector() -> None:
    def different_stat_selected() -> None:
        clear_ph_element(ph_stat)

    select_options = ['Basic statistics',
                      'User collection',
                      'Favourite designers',
                      'H-index',
                      'Games tried grouped by year of publication',
                      'Age of games played',
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
            case "Basic statistics": present_basics()
            case "User collection": present_collection()
            case "Favourite designers": present_favourite_designers()
            case "H-index": present_h_index()
            case "Games tried grouped by year of publication": present_games_by_publication_year()
            case "Age of games played": present_age_of_games_played()
            case "Weight distribution of user's games and plays": present_games_by_weight()
            case "Play statistics by year": present_plays_by_years()
            case "Games known from BGG top list": present_bgg_toplist()
            case "Stat around game weight": present_rankings_and_weights()
            case "Stat around ratings": present_user_and_bgg_ratings()
    return None
