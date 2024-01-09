from datetime import datetime, timedelta, timezone
from threading import Thread
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

from bgg_import.get_functions import get_current_rankings, get_historic_rankings
from bgg_import.import_current_ranking import import_current_ranking
from bgg_import.import_historic_ranking import import_historic_ranking


def check_globals() -> None:
    # TODO redesign with cache delete
    df_current_rankings = get_current_rankings()
    df_historic_rankings = get_historic_rankings()
    import_current_ranking(df_current_rankings)
    import_historic_ranking(df_historic_rankings)
    return None


def check_for_new_data() -> None:
    if "last_checked_globals" not in st.session_state:
        st.session_state.last_checked_globals = str(datetime.now(timezone.utc) - timedelta(minutes=1))
    if str(datetime.now(timezone.utc)) > st.session_state.last_checked_globals:
        thread_check_globals = Thread(target=check_globals)
        thread_check_globals.name = "check_globals"
        add_script_run_ctx(thread_check_globals)
        thread_check_globals.start()
        st.session_state.last_checked_globals = str(datetime.now(timezone.utc) + timedelta(hours=24))
