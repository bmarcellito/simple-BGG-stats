import sys
from time import sleep
from datetime import datetime, timedelta
from requests import get
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from threading import Thread, enumerate

import tracemalloc
import linecache
import gc

from my_logger import timeit, logger
import bgg_stats
import bgg_import

refresh_user_data = 5  # for importing user data - number represents days


def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))


def import_globals() -> None:
    bgg_import.init_load()
    # logging the new session. Can be slow, so it is not the first activity to log :D
    st.session_state.ip = get('https://api.ipify.org').text
    logger.info(f'New session started from {st.session_state.ip}')


def check_globals() -> None:
    st.session_state.global_fresh_ranking = bgg_import.current_ranking(st.session_state.global_fresh_ranking)
    st.session_state.global_historic_ranking = bgg_import.historic_ranking(st.session_state.global_historic_ranking)


@timeit
def import_user_data(username: str, user_page: str, refresh: int) -> None:
    st.session_state.my_collection = bgg_import.user_collection(username=username, user_page=user_page,
                                                                refresh=refresh)
    st.session_state.my_plays = bgg_import.user_plays(username, refresh)
    while (("my_collection" not in st.session_state) or ("my_plays" not in st.session_state)
           or ("global_game_infodb" not in st.session_state)):
        # still loading - has to wait a bit
        sleep(1)
    st.session_state.global_game_infodb, st.session_state.global_play_numdb = (
        bgg_import.build_item_db_all(st.session_state.my_collection, st.session_state.my_plays,
                                     st.session_state.global_game_infodb, st.session_state.global_play_numdb))
    st.session_state.stat_selection = "Basic statistics"


def present_stats(username: str):
    # TODO start report only if all data loaded
    # TODO reports should check whether there is enough data
    # TODO schema for TOP list
    # tracemalloc.start()
    st.title(f'Statistics of {username}')
    option = st.selectbox('Choose a statistic',
                          ('Basic statistics', 'User\'s collection', 'H-index', 'Favourite designers',
                           'Games tried grouped by year of publication',
                           'Play statistics by year', 'Games known from BGG top list',
                           'Stat around game weight', 'Stat around ratings'), key='stat_selection')
    while (("my_collection" not in st.session_state) and ("my_plays" not in st.session_state)
           and ("global_game_infodb" not in st.session_state)):
        # still loading - has to wait a bit
        sleep(1)

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
            bgg_stats.historic_ranking(st.session_state.global_historic_ranking, st.session_state.my_plays)
        case "Stat around game weight":
            bgg_stats.by_weight(st.session_state.global_game_infodb, st.session_state.my_collection,
                                st.session_state.my_plays)
        case "Stat around ratings":
            bgg_stats.by_rating(st.session_state.my_collection, st.session_state.my_plays,
                                st.session_state.global_game_infodb)
    # snapshot = tracemalloc.take_snapshot()
    # display_top(snapshot)


def init() -> None:
    st.session_state.refresh_button_disabled = True
    thread_global_import = Thread(target=import_globals)
    thread_global_import.name = "import_globals"
    add_script_run_ctx(thread_global_import)
    thread_global_import.start()
    st.session_state.user_state = "Init"
    st.session_state.last_checked = str(datetime.now() + timedelta(minutes=5))


def extra_admin():
    # TODO new game appears in a new historic file - what will happen?
    with st.expander("See logs"):
        # st.markdown(f'global_historic_ranking: {sys.getsizeof(st.session_state.global_historic_ranking)}')
        # st.markdown(f'global_game_infodb: {sys.getsizeof(st.session_state.global_game_infodb)}')
        # st.markdown(f'global_fresh_ranking: {sys.getsizeof(st.session_state.global_fresh_ranking)}')
        # st.markdown(f'global_play_numdb: {sys.getsizeof(st.session_state.global_play_numdb)}')
        # st.markdown(f'check_user_cache: {sys.getsizeof(st.session_state.check_user_cache)}')
        gc.collect()
        st.markdown(f'Garbage col: {gc.get_count()}')
        st.markdown("")
        # for thread in enumerate():
        #     st.markdown(thread.name)
    while 0 == 0:
        if ("global_historic_ranking" in st.session_state) and ("global_fresh_ranking" in st.session_state):
            if str(datetime.now()) > st.session_state.last_checked:
                # print("hell yeah")
                thread_check_globals = Thread(target=check_globals)
                thread_check_globals.name = "check_globals"
                add_script_run_ctx(thread_check_globals)
                thread_check_globals.start()
                st.session_state.last_checked = str(datetime.now() + timedelta(hours=24))
        sleep(60*60)


def main():
    with (st.sidebar):
        st.title("BGG statistics")
        with st.form("my_form"):
            bgg_username = st.text_input('Enter a BGG username', key="input_username")
            submitted = st.form_submit_button("Submit")
        st.caption(f'User data is cached for {refresh_user_data} days. Push the button to refresh it')
        if st.button(label="Refresh selected user's data", disabled=st.session_state.refresh_button_disabled):
            with st.status("Reimporting data...", expanded=True):
                bgg_import.user_collection.clear()
                bgg_import.user_plays.clear()
                import_user_data(bgg_username, "", 0)
                # st.rerun()

        if submitted:
            with st.status("Importing data...", expanded=True):
                with st.empty():
                    st.caption("Loading cache...")
                    while "check_user_cache" not in st.session_state:
                        # Check user cache is still loading - has to wait a bit
                        sleep(1)
                st.session_state.user_state = "Loading"
                st.session_state.user_state, user_page, st.session_state.check_user_cache = \
                    bgg_import.check_user(username=bgg_username, df_check_user_cache=st.session_state.check_user_cache)
                if st.session_state.user_state == "User found":
                    import_user_data(bgg_username, user_page, refresh_user_data)
                    del user_page
                    st.session_state.user_state = "Loaded"
                    st.session_state.refresh_button_disabled = False
                else:
                    st.session_state.refresh_button_disabled = True

    # main screen
    while st.session_state.user_state in ["Loading", "User found"]:
        sleep(1)
    if st.session_state.user_state == "Loaded":
        present_stats(bgg_username)
    if st.session_state.user_state in ["Init", "No valid user"]:
        st.title("Statistics")
        if st.session_state.user_state == "Init":
            # no username entered (yet)
            st.write("Enter a user name first!")
        if st.session_state.user_state == "No valid user":
            # non-existing username entered
            st.write("No such user! Enter a new user name!")
        st.write("Use the sidebar on the left! Click the tiny arrow in the top left corner to open it.")
        st.write("")
        bgg_stats.add_description("intro", "description")

    if bgg_username == "bmarcell":
        extra_admin()


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    if "user_state" not in st.session_state:
        init()
    st.markdown("""
                    <html><head><style>
                            ::-webkit-scrollbar {width: 14px; height: 14px;}
                    </style></head><body></body></html>
                """, unsafe_allow_html=True)
    main()
