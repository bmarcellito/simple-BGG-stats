import streamlit as st

from bgg_import.check_user import check_user
from bgg_import import import_user_data
from contact_form import contact_form_button
from main_screen_functions.presentation_hack import clear_ph_element


def user_name_box(main_screen, ph_import) -> None:
    def username_button_pushed(el_main_screen, el_import) -> None:
        if "bgg_username" not in st.session_state:
            st.session_state.bgg_username = ""
        if st.session_state.bgg_username == "":
            st.session_state.user_state = "No_user_selected"
        else:
            st.session_state.importing = "Regular_import"
        clear_ph_element(el_main_screen)
        clear_ph_element(el_import)

    st.text_input('Enter a BGG username and hit enter', key="bgg_username", on_change=username_button_pushed,
                  args=[main_screen, ph_import])
    return None


def user_refresh_box(main_screen, ph_import) -> None:
    def refresh_button_pushed(el_main_screen, el_ph_import) -> None:
        clear_ph_element(el_main_screen)
        clear_ph_element(el_ph_import)
        st.session_state.importing = "Refresh_import"

    if "refresh_button_disabled" not in st.session_state:
        st.session_state.refresh_button_disabled = True
    if not st.session_state.refresh_button_disabled:
        refresh_user_data = st.secrets["refresh_user_data"]
        st.caption(f'Imported user data is cached for {refresh_user_data} days. Push the button to import fresh data')
        st.button(label="Refresh user's data", on_click=refresh_button_pushed, args=[main_screen, ph_import])


def user_import_box() -> None:
    if "importing" not in st.session_state:
        st.session_state.importing = "No_importing"
    match st.session_state.importing:
        case "No_importing":
            with st.status("No importing needed", expanded=False):
                pass
            return None
        case "Refresh_import":
            label = "Reimporting data..."
            refresh_user_data = 0
        case "Regular_import":
            label = "Importing data..."
        case _:
            label = ""

    with st.status(label=label, expanded=True):
        if st.session_state.importing == "Regular_import":
            st.session_state.user_state = "Check_user"
            st.session_state.user_state = check_user(username=st.session_state.bgg_username)
            if st.session_state.user_state == "No_valid_user":
                st.session_state.refresh_button_disabled = True
                st.session_state.importing = "No_importing"
                return None
            refresh_user_data = st.secrets["refresh_user_data"]
        import_user_data(st.session_state.bgg_username, refresh_user_data)

    st.session_state.user_state = "User_imported"
    st.session_state.refresh_button_disabled = False
    st.session_state.importing = "No_importing"
    return None


def contact_form_box(main_screen) -> None:
    contact_form_button(main_screen)


def present_sidebar(main_screen) -> None:
    st.title("BGG statistics")
    ph_interaction = st.empty()
    ph_import = st.empty()
    ph_contact = st.empty()
    with ph_interaction.container():
        user_name_box(main_screen, ph_import)
    with ph_import.container():
        user_import_box()
        user_refresh_box(main_screen, ph_import)
    with ph_contact.container():
        contact_form_box(main_screen)
    return None
