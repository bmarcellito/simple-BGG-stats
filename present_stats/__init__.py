from time import sleep
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
from present_stats.new_stat_selected import new_stat_selected

select_options = ['Basic statistics',
                  'User\'s collection',
                  'H-index',
                  'Favourite designers',
                  'Games tried grouped by year of publication',
                  'Age of games played',
                  'Weight distribution of user\'s games and plays',
                  'Play statistics by year',
                  'Games known from BGG top list',
                  'Stat around game weight',
                  'Stat around ratings']


def change_of_stat() -> None:
    st.session_state.previous_stat = st.session_state.stat_key
    new_stat_selected()


def remember_my_state(username: str) -> None:
    st.session_state.ph_stat_sel = st.empty()
    st.session_state.ph_stat_sel.text = ""
    if "previous_stat" not in st.session_state:
        st.session_state.previous_stat = select_options[0]
    if "stat_state" not in st.session_state:
        st.session_state.stat_state = 0
    if "previous_user" in st.session_state:
        if st.session_state.previous_user != username:
            st.session_state.stat_state = 0
        else:
            st.session_state.stat_state = select_options.index(st.session_state.previous_stat)
    st.session_state.previous_user = username


def present_stat_selector(username: str) -> None:
    st.title(f'Statistics of {username}')
    remember_my_state(username)

    with st.session_state.ph_stat_sel.container():
        option = st.selectbox(label='Choose a statistic', options=select_options, on_change=change_of_stat,
                              index=st.session_state.stat_state, key="stat_key")
    while "global_game_infodb" not in st.session_state:
        # still loading - has to wait a bit
        sleep(1)

    match option:
        case "Basic statistics":
            present_basics()
        case "User\'s collection":
            present_collection()
        case "Favourite designers":
            present_favourite_designers()
        case "H-index":
            present_h_index()
        case "Games tried grouped by year of publication":
            present_games_by_publication_year()
        case "Age of games played":
            present_age_of_games_played()
        case "Weight distribution of user's games and plays":
            present_games_by_weight()
        case "Play statistics by year":
            present_plays_by_years()
        case "Games known from BGG top list":
            present_bgg_toplist()
        case "Stat around game weight":
            present_rankings_and_weights()
        case "Stat around ratings":
            present_user_and_bgg_ratings()
    return None
