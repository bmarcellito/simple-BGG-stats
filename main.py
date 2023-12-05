from datetime import datetime, timedelta

import streamlit as st

from my_logger import getlogger
import bgg_stats
import gdrive
import bgg_import


def main():
    gdrive_original = st.secrets["gdrive_original"]
    gdrive_processed = st.secrets["gdrive_processed"]
    gdrive_user = st.secrets["gdrive_user"]
    refresh_user_data = 5  # for importing user data - number represents days

    st.set_page_config(layout="wide")
    if "user_exist" not in st.session_state:
        st.session_state.user_exist = False
        st.session_state.logger, st.session_state.syslog = getlogger()
        st.session_state.logger.info(f'New session started!')
    if "refresh_disabled" not in st.session_state:
        st.session_state.refresh_disabled = True
    my_service = gdrive.authenticate()
    st.markdown("""
                    <html><head><style>
                            ::-webkit-scrollbar {
                                width: 14px;
                                height: 14px;}
                    </style></head><body></body></html>
                """, unsafe_allow_html=True)
    with (st.sidebar):
        st.title("BGG statistics")

        with st.form("my_form"):
            bgg_username = st.text_input('Enter a BGG username', key="input_username")
            submitted = st.form_submit_button("Submit")

        # if st.session_state.user_exist:
        st.caption(f'User data is cached for {refresh_user_data} days. Push the button to refresh it')
        if st.button(label="Refresh selected user's data", disabled=st.session_state.refresh_disabled):
            bgg_import.delete_user_info(my_service, bgg_username, st.session_state.logger)
            bgg_import.user_collection.clear()
            bgg_import.user_plays.clear()
            submitted = True

        if submitted:
            with st.status("Importing data...", expanded=True) as status:
                st.session_state.logger.info(f'Username entered: {bgg_username}')
                st.session_state.stat_selection = "Basic statistics"
                st.session_state.user_exist, st.session_state.user_folder = bgg_import.check_user(
                    my_service, bgg_username, gdrive_user, st.session_state.logger)
                if not st.session_state.user_exist:
                    status.update(label="No valid user!", state="error", expanded=False)
                    st.session_state.refresh_disabled = True
                    st.rerun()

                st.session_state.refresh_disabled = False
                if st.session_state.user_exist:
                    st.session_state.my_plays = bgg_import.user_plays(
                        my_service, bgg_username, st.session_state.user_folder, refresh_user_data,
                        st.session_state.logger)
                    st.session_state.my_collection = bgg_import.user_collection(
                        my_service, bgg_username, st.session_state.user_folder, refresh_user_data,
                        st.session_state.logger)
                    bgg_import.build_game_db(my_service, gdrive_processed, st.session_state.my_collection,
                                             st.session_state.logger)
                    st.session_state.global_game_infodb, st.session_state.global_play_numdb = bgg_import\
                        .build_game_db(my_service, gdrive_processed, st.session_state.my_plays, st.session_state.logger)
                    if "last_imported" not in st.session_state:
                        st.session_state.last_imported = datetime.now()-timedelta(days=1)
                    if datetime.now() > st.session_state.last_imported:
                        bgg_import.current_ranking.clear()
                        bgg_import.historic_ranking.clear()
                        st.session_state.global_fresh_ranking = bgg_import.current_ranking(
                            my_service, gdrive_original, gdrive_processed, st.session_state.logger)
                        st.session_state.global_historic_rankings = bgg_import.historic_ranking(
                            my_service, gdrive_original, gdrive_processed,
                            st.session_state.global_fresh_ranking, st.session_state.logger)
                        st.session_state.last_imported = datetime.now()+timedelta(days=1)
                    status.update(label="Importing complete!", state="complete", expanded=False)
                st.rerun()

    if st.session_state.user_exist:
        no_data = (st.session_state.my_collection.empty or st.session_state.my_plays.empty or
                   st.session_state.global_fresh_ranking.empty or st.session_state.global_historic_rankings.empty or
                   st.session_state.global_game_infodb.empty)
        if not no_data:
            # user has enough information to present statistics
            st.title(f'Statistics of {bgg_username}')
            option = st.selectbox('Choose a statistic',
                                  ('Basic statistics', 'User\'s collection', 'Favourites',
                                   'H-index', 'Games tried grouped by year of publication',
                                   'Play statistics by year', 'Games known from BGG top list',
                                   'Stat around game weight', 'Stat around ratings'), key='stat_selection')
            match option:
                case "Basic statistics":
                    bgg_stats.basics(st.session_state.my_collection, st.session_state.my_plays,
                                     st.session_state.global_game_infodb)
                    # bgg_stats.plays_by_publication(my_plays, my_collection, global_game_infodb)
                    # bgg_stats.stat_not_played(my_collection)
                case "User\'s collection":
                    bgg_stats.collection(st.session_state.my_collection, st.session_state.global_game_infodb,
                                         st.session_state.global_play_numdb)
                case "Favourites":
                    opt_fav = st.selectbox('Choose a topic', ('Favourite games', 'Favourites Designers'),
                                           key='stat_fav')
                    match opt_fav:
                        case 'Favourite games':
                            bgg_stats.favourite_games(st.session_state.my_collection,
                                                      st.session_state.global_game_infodb)
                        case 'Favourites Designers':
                            bgg_stats.favourite_designers(st.session_state.my_collection,
                                                          st.session_state.global_game_infodb)
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
        else:
            # user exists but no information
            st.title("Statistics")
            if st.session_state.global_fresh_ranking.empty or st.session_state.global_historic_rankings.empty:
                st.write("Missing general information. Come back later :(")
            else:
                st.write("The selected user has not enough information to show statistics. Enter a new user name!")
    else:
        # no valid user selected
        st.title("Statistics")
        st.write("Enter a user name first!")
        st.write("Use the sidebar on the left! Click the tiny arrow in the top left corner to open it.")


if __name__ == "__main__":
    main()
    # csak különbségek átadása mentésre!
    # TODO schema for TOP list
    # TODO new game appears in  a new historic file - what will happen?
