from datetime import datetime, timedelta
from threading import Thread
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

from bgg_import.get_current_ranking import get_current_ranking
from bgg_import.get_historic_ranking import get_historic_ranking


def check_globals() -> None:
    st.session_state.global_fresh_ranking = get_current_ranking(st.session_state.global_fresh_ranking)
    st.session_state.global_historic_ranking = get_historic_ranking(st.session_state.global_historic_ranking)


def check_for_new_data() -> None:
    if ("global_historic_ranking" in st.session_state) and ("global_fresh_ranking" in st.session_state):
        if "last_checked_globals" not in st.session_state:
            st.session_state.last_checked_globals = str(datetime.now() - timedelta(minutes=1))
        if str(datetime.now()) > st.session_state.last_checked_globals:
            thread_check_globals = Thread(target=check_globals)
            thread_check_globals.name = "check_globals"
            add_script_run_ctx(thread_check_globals)
            thread_check_globals.start()
            st.session_state.last_checked = str(datetime.now() + timedelta(hours=24))
