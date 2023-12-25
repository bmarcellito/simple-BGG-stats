from time import sleep
from datetime import datetime, timedelta
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from threading import Thread
# import gc

from presentation_hack import username_button_pushed, refresh_button_pushed
from bgg_import.check_user import check_user
from bgg_import import import_user_data
from bgg_import.get_user_collection import user_collection
from bgg_import.get_user_plays import user_plays
from bgg_import.get_current_ranking import get_current_ranking
from bgg_import.get_historic_ranking import historic_ranking
from bgg_import.init_load import init_load
from present_stats import present_stats

refresh_user_data = 5  # for importing user data - number represents days


def check_globals() -> None:
    st.session_state.global_fresh_ranking = get_current_ranking(st.session_state.global_fresh_ranking)
    st.session_state.global_historic_ranking = historic_ranking(st.session_state.global_historic_ranking)


def init() -> None:
    thread_global_import = Thread(target=init_load)
    thread_global_import.name = "import_globals"
    add_script_run_ctx(thread_global_import)
    thread_global_import.start()

    st.session_state.bgg_username = ""
    st.session_state.refresh_button_disabled = True
    st.session_state.user_state = "No_user_selected"
    st.session_state.last_checked = str(datetime.now() + timedelta(minutes=5))
    st.session_state.stat_state = 0
    st.session_state.can_present = True


def check_for_new_data() -> None:
    if ("global_historic_ranking" in st.session_state) and ("global_fresh_ranking" in st.session_state):
        if str(datetime.now()) > st.session_state.last_checked:
            thread_check_globals = Thread(target=check_globals)
            thread_check_globals.name = "check_globals"
            add_script_run_ctx(thread_check_globals)
            thread_check_globals.start()
            st.session_state.last_checked = str(datetime.now() + timedelta(hours=24))


def extra_admin() -> None:
    pass
    # if bgg_username == "bmarcell":
    #     with st.expander("See logs"):
    #         gc.collect()
    #         st.markdown(f'Garbage col: {gc.get_count()}')


def contact_form() -> None:
    st.session_state.ph_contact = st.empty()
    if st.session_state.ph_contact.button("Send feedback!"):
        st.session_state.previous_user_state = st.session_state.user_state
        st.session_state.user_state = "Contact_form"


def sidebar() -> str:
    with st.sidebar:
        st.title("BGG statistics")
        with st.form("my_form"):
            st.session_state.bgg_username = st.text_input('Enter a BGG username', key="input_username")
            submitted = st.form_submit_button(label="Submit", on_click=username_button_pushed)
        st.caption(f'User data is cached for {refresh_user_data} days. Push the button to refresh it')
        if st.session_state.user_state == "User_found":
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

        if submitted:
            st.session_state.ph_import = st.empty()
            st.session_state.ph_import.empty()
            sleep(0.1)
            with st.session_state.ph_import.status("Importing data...", expanded=True):
                st.session_state.can_present = False
                st.session_state.user_state = check_user(username=st.session_state.bgg_username)
                if st.session_state.user_state == "User_found":
                    import_user_data(st.session_state.bgg_username, refresh_user_data)
                    st.session_state.user_state = "User_freshly_imported"
                st.session_state.can_present = True
            st.rerun()
        else:
            with st.status("Importing data...", expanded=False):
                pass
        contact_form()
        return st.session_state.bgg_username


def main():
    st.session_state.bgg_username = sidebar()
    if st.session_state.can_present:
        present_stats(st.session_state.bgg_username)
    # extra_admin()
    check_for_new_data()


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
    # TODO new game appears in a new historic file - what will happen?
    # TODO contact form so user can send feedback
    # TODO schema for BGG TOP list
    # TODO stat for every year: average publication year / complexity of games tried
    # TODO stat for every year: average publication year / complexity of games played
    # TODO stat for every year: average publication year / complexity of games known
    # TODO favor games: plays with top10 games in time
    # TODO favor games: most played game every year
    # TODO favor games: highest rated game for every year by publication year
    # TODO favor games: highest rated game for every year among the newly tried games that year
    # TODO stat: % of newly tried games - how many were published that year / earlier
