from time import sleep
from requests import get
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from threading import Thread, Lock

import my_logger
from my_logger import getlogger
import bgg_stats
import bgg_import


# TODO locking!!!
def import_globals() -> None:
    # first we load all available global data files
    bgg_import.init_load()
    st.session_state.ip = get('https://api.ipify.org').text
    st.session_state.logger.info(f'New session started from {st.session_state.ip}')
    # daily check of new data files in the background until the website runs
    while 0 == 0:
        st.session_state.global_fresh_ranking = bgg_import.current_ranking()
        st.session_state.global_historic_rankings = bgg_import.historic_ranking(st.session_state.global_fresh_ranking)
        sleep(60*60*24)


def init():
    st.session_state.logger = getlogger(__name__)
    st.session_state.logger.propagate = False
    st.session_state.refresh_button_disabled = True
    st.session_state.user_state = "Init"

    thread_global_import = Thread(target=import_globals)
    add_script_run_ctx(thread_global_import)
    thread_global_import.start()


@my_logger.timeit
def import_user_data(username, refresh: int) -> None:
    st.session_state.my_collection = bgg_import.user_collection(username=username, refresh=refresh)
    st.session_state.my_plays = bgg_import.user_plays(username, refresh)
    bgg_import.build_item_db_game(st.session_state.my_collection)
    st.session_state.global_game_infodb, st.session_state.global_play_numdb = bgg_import \
        .build_item_db_play(st.session_state.my_plays)
    st.session_state.stat_selection = "Basic statistics"


def present_stats(username: str):
    st.title(f'Statistics of {username}')
    option = st.selectbox('Choose a statistic',
                          ('Basic statistics', 'User\'s collection', 'H-index', 'Favourite designers',
                           'Games tried grouped by year of publication',
                           'Play statistics by year', 'Games known from BGG top list',
                           'Stat around game weight', 'Stat around ratings'), key='stat_selection')
    match option:
        case "Basic statistics":
            bgg_stats.basics(st.session_state.my_collection, st.session_state.my_plays,
                             st.session_state.global_game_infodb)
            # bgg_stats.favourite_games(st.session_state.my_collection, st.session_state.global_game_infodb)
            # bgg_stats.plays_by_publication(my_plays, my_collection, global_game_infodb)
            # bgg_stats.stat_not_played(my_collection)
        case "User\'s collection":
            bgg_stats.collection(st.session_state.my_collection, st.session_state.global_game_infodb,
                                 st.session_state.global_play_numdb)
        case "Favourite designers":
            bgg_stats.favourite_designers(st.session_state.my_collection, st.session_state.global_game_infodb)
        case "H-index":
            bgg_stats.h_index(st.session_state.my_plays, st.session_state.global_game_infodb)
        case "Games tried grouped by year of publication":
            bgg_stats.games_by_publication(st.session_state.my_collection, st.session_state.global_game_infodb)
        case "Play statistics by year":
            bgg_stats.yearly_plays(st.session_state.my_plays)
        case "Games known from BGG top list":
            bgg_stats.historic_ranking(st.session_state.global_historic_rankings, st.session_state.my_plays)
        case "Stat around game weight":
            bgg_stats.by_weight(st.session_state.global_game_infodb, st.session_state.my_collection,
                                st.session_state.my_plays)
        case "Stat around ratings":
            bgg_stats.by_rating(st.session_state.my_collection, st.session_state.my_plays,
                                st.session_state.global_game_infodb)


def main():
    refresh_user_data = 5  # for importing user data - number represents days
    if "user_state" not in st.session_state:
        init()

    st.set_page_config(layout="wide")
    st.markdown("""
                    <html><head><style>
                            ::-webkit-scrollbar {width: 14px; height: 14px;}
                    </style></head><body></body></html>
                """, unsafe_allow_html=True)

    with (st.sidebar):
        st.title("BGG statistics")

        with st.form("my_form"):
            bgg_username = st.text_input('Enter a BGG username', key="input_username")
            submitted = st.form_submit_button("Submit")

        st.caption(f'User data is cached for {refresh_user_data} days. Push the button to refresh it')
        if st.button(label="Refresh selected user's data", disabled=st.session_state.refresh_button_disabled):
            with st.status("Reimporting data...", expanded=True):
                import_user_data(bgg_username, 0)
                st.rerun()

        if submitted:
            with st.status("Importing data...", expanded=True):
                st.session_state.refresh_button_disabled = True
                if bgg_username == "":
                    st.session_state.user_state = "Init"
                    st.rerun()
                st.session_state.user_state = bgg_import.check_user(username=bgg_username)
                if st.session_state.user_state in ["No valid user", "Init"]:
                    st.rerun()
                import_user_data(bgg_username, refresh_user_data)
                st.session_state.refresh_button_disabled = False
                st.rerun()

    if st.session_state.user_state == "User found":
        if "global_historic_rankings" not in st.session_state:
            # global game information is still loading in the other thread - has to wait a bit!
            st.write("Global game information is still loading. Please wait...")
            while "global_historic_rankings" not in st.session_state:
                sleep(1)
            st.rerun()
        if st.session_state.global_fresh_ranking.empty or st.session_state.global_historic_rankings.empty:
            # cannot find global game information - cannot show any statistics. Website halts
            st.write("Missing general information. Currently the site does not work. Come back later :(")
            exit(0)
        if st.session_state.my_collection.empty or st.session_state.my_plays.empty:
            # user exists but no information
            st.title("Statistics")
            st.write("The selected user has not enough information to show statistics. Enter a new user name!")
        else:
            # user has enough information to present statistics
            present_stats(bgg_username)

    if st.session_state.user_state == "Init":
        # no username entered (yet)
        st.title("Statistics")
        st.write("Enter a user name first!")
        st.write("Use the sidebar on the left! Click the tiny arrow in the top left corner to open it.")
        st.write("")
        bgg_stats.add_description("intro", "description")

    if st.session_state.user_state == "No valid user":
        # non-existing username entered
        st.title("Statistics")
        st.write("No such user! Enter a new user name!")
        st.write("Use the sidebar on the left! Click the tiny arrow in the top left corner to open it.")
        st.write("")
        bgg_stats.add_description("intro", "description")


if __name__ == "__main__":
    main()
    # csak különbségek átadása mentésre!
    # TODO schema for TOP list
    # TODO new game appears in a new historic file - what will happen?
