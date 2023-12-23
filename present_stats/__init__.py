from time import sleep
import streamlit as st

from present_stats.basics import present_basics
from present_stats.collection import present_collection
from present_stats.h_index import present_h_index
from present_stats.favourite_designers import present_favourite_designers
from present_stats.games_by_publication_year import present_games_by_publication_year
from present_stats.games_by_weight import present_games_by_weight
from present_stats.plays_by_years import present_plays_by_years
from present_stats.bgg_toplist import present_bgg_toplist
from present_stats.rankings_and_weights import present_rankings_and_weights
from present_stats.user_and_bgg_ratings import present_user_and_bgg_ratings
from present_stats.add_description import add_description
from present_stats.missing_stat import present_starting_screen, present_invalid_user
from presentation_hack import new_stat_selected


def present_stat_selector(username: str) -> None:
    st.title(f'Statistics of {username}')
    select_options = ['Basic statistics', 'User\'s collection', 'H-index', 'Favourite designers',
                      'Games tried grouped by year of publication', "Weight distribution of user's games and plays",
                      'Play statistics by year', 'Games known from BGG top list', 'Stat around game weight',
                      'Stat around ratings']
    option = st.selectbox('Choose a statistic', select_options, key='stat_selection', on_change=new_stat_selected)
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


def present_stats(username: str, user_state: str):
    # TODO start report only if all data loaded or reports should check whether there is enough data
    # TODO schema for TOP list
    match user_state:
        case "No_user_selected":
            present_starting_screen()
        case "No_valid_user":
            present_invalid_user()
        case "User_found":
            present_stat_selector(username)
    return None
