import streamlit as st

from main_screen_functions.bgg_data_class import BggData
from bgg_import.check_user import check_user, get_user_folder
from bgg_import import import_user_data
from contact_form import contact_form_button
from main_screen_functions.presentation_hack import clear_ph_element
from main_screen_functions.extra_admin import admin_button
from my_logger import log_info, log_error


def user_name_box(main_screen, ph_import) -> None:
    def username_button_pushed(el_main_screen, el_import) -> None:
        st.session_state.app_state = "User_view"
        if "bgg_username" not in st.session_state:
            st.session_state.bgg_username = ""
        if st.session_state.bgg_username == "":
            st.session_state.user_state = "No_user_selected"
        else:
            st.session_state.user_state = "Regular_import"
            if st.secrets["environment"] == "live":
                log_info(f'Query of {st.session_state.bgg_username} started')
        clear_ph_element([el_main_screen, el_import])

    label = 'Enter a BGG username and hit enter'
    st.text_input(label=label, key="bgg_username", on_change=username_button_pushed, args=[main_screen, ph_import])
    return None


def user_refresh_box(main_screen, ph_import) -> None:
    def refresh_button_pushed(el_main_screen, el_ph_import) -> None:
        st.session_state.user_state = "Refresh_import"
        clear_ph_element([el_main_screen, el_ph_import])

    if st.session_state.user_state == "User_imported":
        refresh_user_data = st.secrets["refresh_user_data"]
        st.caption(f'Imported user data is cached for {refresh_user_data} days. Push the button to import fresh data')
        st.button(label="Refresh user's data", on_click=refresh_button_pushed, args=[main_screen, ph_import])


def user_import_box() -> BggData:
    with (st.status("Importing data...", expanded=True)):
        answer = check_user(username=st.session_state.bgg_username)
        if answer in ["No_user_selected", "No_valid_user", "Import_error"]:
            st.session_state.user_state = answer
            return BggData()

        if st.session_state.user_state == "Refresh_import":
            refresh_user_data = 0
        else:
            refresh_user_data = st.secrets["refresh_user_data"]
        folder_id = get_user_folder(username=st.session_state.bgg_username)
        if folder_id == 0:
            st.session_state.user_state = "Import_error"
            log_error(f'user_import_box - user folder is missing: {st.session_state.bgg_username}')
            return BggData()
        my_bgg_data = import_user_data(st.session_state.bgg_username, folder_id, refresh_user_data)
        st.session_state.user_state = "User_imported"
    return my_bgg_data


def present_sidebar(main_screen) -> BggData:
    st.title("BGG statistics")
    ph_interaction = st.empty()
    ph_import = st.empty()
    with ph_interaction.container():
        user_name_box(main_screen, ph_import)
    with ph_import.container():
        my_bgg_data = user_import_box()
        user_refresh_box(main_screen, ph_import)
    contact_form_button(main_screen)
    if st.secrets["environment"] == "dev":
        admin_button(main_screen)
    return my_bgg_data
