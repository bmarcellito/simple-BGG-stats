from time import sleep

import streamlit as st


def new_stat_selected() -> None:
    if "ph_stat" in st.session_state:
        st.session_state.ph_stat.empty()
        sleep(0.1)
        st.session_state.ph_stat.empty()
        sleep(0.1)
        st.session_state.ph_stat.empty()
        sleep(0.1)
