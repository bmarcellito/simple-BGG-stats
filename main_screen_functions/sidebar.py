from time import sleep
import streamlit as st

from bgg_import import user_collection, user_plays, import_user_data
from bgg_import.check_user import check_user
from contact_form import contact_form_button
from main_screen_functions.presentation_hack import username_button_pushed, refresh_button_pushed


def user_name_box() -> str:
    with st.form("my_form"):
        st.session_state.bgg_username = st.text_input('Enter a BGG username', key="input_username")
        submitted = st.form_submit_button(label="Submit", on_click=username_button_pushed)
    refresh_user_data = st.secrets["refresh_user_data"]
    st.caption(f'User data is cached for {refresh_user_data} days. Push the button to refresh it')
    return submitted


def user_refresh_box() -> None:
    if st.session_state.user_state == "User_imported":
        button_disabled = False
    else:
        button_disabled = True
    if st.button(label="Refresh selected user's data", disabled=button_disabled, on_click=refresh_button_pushed):
        st.session_state.ph_import = st.empty()
        st.session_state.ph_import.empty()
        sleep(0.1)
        with st.session_state.ph_import.status("Reimporting data...", expanded=True):
            user_collection.clear()
            user_plays.clear()
            import_user_data(st.session_state.bgg_username, 0)


def user_import_box(submitted: str) -> None:
    if submitted:
        st.session_state.ph_import = st.empty()
        st.session_state.ph_import.empty()
        sleep(0.1)
        with st.session_state.ph_import.status("Importing data...", expanded=True):
            st.session_state.user_state = "Check_user"
            st.session_state.user_state = check_user(username=st.session_state.bgg_username)
            if st.session_state.user_state == "User_found":
                refresh_user_data = st.secrets["refresh_user_data"]
                import_user_data(st.session_state.bgg_username, refresh_user_data)
                st.session_state.user_state = "User_imported"
        st.rerun()
    else:
        with st.status("Importing data...", expanded=False):
            pass


def contact_form_box() -> None:
    contact_form_button()


def sidebar() -> None:
    with st.sidebar:
        st.title("BGG statistics")
        submitted = user_name_box()
        user_refresh_box()
        user_import_box(submitted)
        contact_form_box()
        return None
