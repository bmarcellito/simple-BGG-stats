# dataframes

# reading historical scraped files

# WEB interface
import streamlit as st

# google drive

import bgg_stats
import gdrive
import bgg_import


def main():
    # TODO schema for TOP list
    gdrive_original = st.secrets["gdrive_original"]
    gdrive_processed = st.secrets["gdrive_processed"]
    gdrive_user = st.secrets["gdrive_user"]
    REFRESH_USER_DATA = 3  # for importing user data - number represents days

    if 'sidebar_state' not in st.session_state:
        st.session_state.sidebar_state = 'expanded'
    st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state, layout="wide")

    my_service = gdrive.authenticate()

    if "user_exist" not in st.session_state:
        st.session_state.user_exist = False

    with st.sidebar:
        st.title("BGG statistics")

        with st.form("my_form"):
            bgg_username = st.text_input('Enter a BGG username', key="input_username")
            submitted = st.form_submit_button("Submit")
            if submitted:
                st.session_state.stat_selection = "Basic statistics"
                st.session_state.user_exist = bgg_import.check_user(my_service, bgg_username, gdrive_user)
                if (not st.session_state.user_exist) and ('handler' in st.session_state):
                    del st.session_state["handler"]

        st.caption("User data is cached for 3 days. Push the button if you want to have fresh data")
        if st.button(label="Refresh selected user's data"):
            bgg_import.user_collection(my_service, bgg_username, 0)
            bgg_import.user_plays(my_service, bgg_username, 0)

        if submitted:
            st.session_state.stat_selection = "Basic statistics"
            st.session_state.user_exist = bgg_import.check_user(my_service, bgg_username, gdrive_user)
            if (not st.session_state.user_exist) and ('handler' in st.session_state):
                del st.session_state["handler"]

        if st.session_state.user_exist:
            placeholder = st.empty()
            with placeholder.container():
                st.subheader("Importing...")
                # my_: data that is user specific
                my_collection = bgg_import.user_collection(my_service, bgg_username, REFRESH_USER_DATA)
                my_plays = bgg_import.user_plays(my_service, bgg_username, REFRESH_USER_DATA)
                # global_: data independent from user
                bgg_import.build_game_db(my_service, gdrive_processed, my_collection)
                global_game_infodb, global_play_numdb = bgg_import.build_game_db(my_service, gdrive_processed, my_plays)
                global_fresh_ranking = bgg_import.current_ranking(my_service, gdrive_processed)
                global_historic_rankings = bgg_import.historic_ranking(my_service, gdrive_original, gdrive_processed,
                                                                       global_fresh_ranking)
                st.write("IMPORTING / LOADING has finished!\n")
            placeholder.empty()

    if st.session_state.user_exist:
        if not (my_collection.empty or my_plays.empty):
            # user has enough information to present statistics
            st.title(f'Statistics of {bgg_username}')
            option = st.selectbox('Choose a statistic',
                                  ('Basic statistics', 'User\'s collection', 'Favourites',
                                   'H-index', 'Games tried grouped by year of publication',
                                   'Play statistics by year', 'Games known from BGG top list',
                                   'Stat around game weight', 'Stat around ratings'), key='stat_selection')
            match option:
                case "Basic statistics":
                    bgg_stats.basics(my_collection, my_plays, global_game_infodb)
                    # bgg_stats.plays_by_publication(my_plays, my_collection, global_game_infodb)
                    # bgg_stats.stat_not_played(my_collection)
                case "User\'s collection":
                    bgg_stats.collection(my_collection, global_game_infodb, global_play_numdb)
                case "Favourites":
                    opt_fav = st.selectbox('Choose a topic', ('Favourite games', 'Favourites Designers'),
                                           key='stat_fav')
                    match opt_fav:
                        case 'Favourite games':
                            bgg_stats.favourite_games(my_collection, global_game_infodb)
                        case 'Favourites Designers':
                            bgg_stats.favourite_designers(my_collection, global_game_infodb)
                case "H-index":
                    bgg_stats.h_index(my_plays, global_game_infodb)
                case "Games tried grouped by year of publication":
                    bgg_stats.games_by_publication(my_collection, global_game_infodb)
                case "Play statistics by year":
                    bgg_stats.yearly_plays(my_plays)
                case "Games known from BGG top list":
                    bgg_stats.historic_ranking(global_historic_rankings, my_plays)
                case "Stat around game weight":
                    bgg_stats.by_weight(global_game_infodb, my_collection, my_plays)
                case "Stat around ratings":
                    bgg_stats.by_rating(my_collection, my_plays, global_game_infodb)
        else:
            # user exists but no information
            st.title("Statistics")
            st.write("The selected user has not enough information to show statistics. Enter a user name first!")
    else:
        # no valid user selected
        st.title("Statistics")
        st.write("Enter a user name first!")
        st.write("Use the sidebar on the left! Click the tiny arrow in the top left corner to open it.")


if __name__ == "__main__":
    main()
