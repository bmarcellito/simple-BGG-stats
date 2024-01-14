import streamlit as st

from main_screen_functions.bgg_data_class import BggData
from main_screen_functions.presentation_hack import presentation_hack
from bgg_import.init_load import init_load
from main_screen_functions.sidebar import present_sidebar
from present_stats import present_stat_selector
from main_screen_functions.present_invalid_user import present_invalid_user
from main_screen_functions.present_starting_screen import present_starting_screen
from main_screen_functions.present_input_error import present_input_error
from contact_form import contact_form
from bgg_import.check_for_new_data import check_for_new_data
if st.secrets["environment"] == "dev":
    from main_screen_functions.extra_admin import extra_admin


def present_main_screen(main_screen, my_bgg_data: BggData) -> None:
    match st.session_state.app_state:
        case "User_view":
            match st.session_state.user_state:
                case "User_imported": present_stat_selector(my_bgg_data)
                case "No_user_selected": present_starting_screen()
                case "No_valid_user": present_invalid_user()
                case "Input_error": present_input_error()
        case "Contact_form": contact_form(main_screen)
        case "Admin": extra_admin(my_bgg_data, main_screen)


def main():
    sidebar = st.sidebar.empty()
    main_screen = st.empty()
    with sidebar.container():
        my_bgg_data = present_sidebar(main_screen)
    with main_screen.container():
        present_main_screen(main_screen, my_bgg_data)
        check_for_new_data()
    del my_bgg_data


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    presentation_hack()
    if "app_state" not in st.session_state:
        init_load()
        st.session_state.app_state = "User_view"
        st.session_state.user_state = "No_user_selected"
    main()

    # TODO import class - response, status + specific data class??? + öröklés?
    # TODO file reading, web reading no endless loop, but give up sometimes
    # TODO google load timeout handle
    # TODO remove not used columns to save memory
    # TODO historic ranks: best rank counts objectID as well -> error
    # TODO remove prev_owned, trade, ... from collection
    # TODO collection type can be shorter: "b" / "e"
    # TODO collection last modified can be just date
    # TODO remove item name from collection
    # TODO remove comments, item name from plays
    # TODO plays with multiple quantity -> multiple row so no quantity column needed?
    # TODO import could create some merge and delete basic info
    # TODO some stat calculation can be separated into multiple functions
    # TODO cache writing semaphore
    # TODO change token mgmt - separate token for each file
    # TODO new game appears in a new historic file - what will happen?
    # TODO stat for every year: average publication year / complexity of games tried
    # TODO stat for every year: average publication year / complexity of games played
    # TODO stat for every year: average publication year / complexity of games known
    # TODO favor games: most played game every year
    # TODO favor games: highest rated game for every year by publication year
    # TODO favor games: highest rated game for every year among the newly tried games that year
    # TODO stat: % of newly tried games - how many were published that year / earlier
    # TODO datetime.now should be based on server time
    # TODO schema for BGG TOP list
