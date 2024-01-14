import streamlit as st

from main_screen_functions.presentation_hack import clear_ph_element
from main_screen_functions.bgg_data_class import BggData
import gc
from sys import getsizeof


def admin_button(main_screen) -> None:
    def admin_button_pushed(el_main_screen) -> None:
        st.session_state.app_state = "Admin"
        clear_ph_element([el_main_screen])

    st.button(label="Admin", on_click=admin_button_pushed, args=[main_screen])


def extra_admin(my_bgg_data: BggData, main_screen) -> None:
    def back_button_pushed(el_main_screen) -> None:
        st.session_state.app_state = "User_view"
        clear_ph_element([el_main_screen])

    ph_admin = st.empty()
    with ph_admin.container():
        st.title("Admin")
        st.write(f'Size of collection: {getsizeof(my_bgg_data.user_collection):,}')
        st.write(f'Size of plays: {getsizeof(my_bgg_data.user_plays):,}')
        st.write(f'Size of game DB: {getsizeof(my_bgg_data.game_info_db):,}')
        st.write(f'Size of play numbers: {getsizeof(my_bgg_data.play_no_db):,}')
        st.write(f'Amount of variables before garbage collection: {gc.get_count()}')
        with st.expander("Session state"):
            st.write(f'Size of session state: {getsizeof(st.session_state)}')
            st.write(st.session_state)
        with st.expander("User collection"):
            st.write(my_bgg_data.user_collection)
        with st.expander("User plays"):
            st.write(my_bgg_data.user_plays)
        with st.expander("Item DB"):
            st.write(my_bgg_data.game_info_db)
        with st.expander("Play number DB"):
            st.write(my_bgg_data.play_no_db)
        with st.expander("Username cache"):
            st.write(my_bgg_data.username_cache)
        # with st.expander("Current ranking"):
        #     st.write(my_bgg_data.current_rankings)
        # with st.expander("Historical ranking"):
        #     st.write(my_bgg_data.historical_rankings)
        st.button(label='Back to the statistics', on_click=back_button_pushed, args=[main_screen])

