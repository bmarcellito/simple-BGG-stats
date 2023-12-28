import streamlit as st

from main_screen_functions.presentation_hack import presentation_hack
from bgg_import.init_load import initial_load
from main_screen_functions.sidebar import sidebar
from present_stats import present_stat_selector
from main_screen_functions.present_invalid_user import present_invalid_user
from main_screen_functions.present_starting_screen import present_starting_screen
from contact_form import contact_form
from main_screen_functions.extra_admin import extra_admin
from bgg_import.check_for_new_data import check_for_new_data


def main_screen() -> None:
    match st.session_state.user_state:
        case "User_imported":
            present_stat_selector(st.session_state.bgg_username)
        case "No_user_selected":
            present_starting_screen()
        case "No_valid_user":
            present_invalid_user()
        case "Contact_form":
            contact_form()


def main():
    sidebar()
    main_screen()
    check_for_new_data()
    extra_admin()


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    presentation_hack()
    if "user_state" not in st.session_state:
        initial_load()
        st.session_state.user_state = "No_user_selected"
    main()

    # TODO remove not used columns from globals and collections to save memory
    # TODO new game appears in a new historic file - what will happen?
    # TODO schema for BGG TOP list
    # TODO stat for every year: average publication year / complexity of games tried
    # TODO stat for every year: average publication year / complexity of games played
    # TODO stat for every year: average publication year / complexity of games known
    # TODO favor games: plays with top10 games in time
    # TODO favor games: most played game every year
    # TODO favor games: highest rated game for every year by publication year
    # TODO favor games: highest rated game for every year among the newly tried games that year
    # TODO stat: % of newly tried games - how many were published that year / earlier
