import time
import streamlit as st


def new_stat_selected() -> None:
    if "ph_stat" in st.session_state:
        st.session_state.ph_stat.empty()
        time.sleep(0.1)
        st.session_state.ph_stat.empty()
        time.sleep(0.1)
        st.session_state.ph_stat.empty()
        time.sleep(0.1)


def username_button_pushed() -> None:
    if "ph_import" in st.session_state:
        st.session_state.ph_import.empty()
        time.sleep(0.1)
        st.session_state.ph_import.empty()
        time.sleep(0.1)
        st.session_state.ph_import.empty()
        time.sleep(0.1)
    if "ph_stat" in st.session_state:
        st.session_state.ph_stat.empty()
        time.sleep(0.1)
        st.session_state.ph_stat.empty()
        time.sleep(0.1)
        st.session_state.ph_stat.empty()
        time.sleep(0.1)


def refresh_button_pushed() -> None:
    if "ph_import" in st.session_state:
        st.session_state.ph_import.empty()
        time.sleep(0.1)
        st.session_state.ph_import.empty()
        time.sleep(0.1)
        st.session_state.ph_import.empty()
        time.sleep(0.1)
    if "ph_stat" in st.session_state:
        st.session_state.ph_stat.empty()
        time.sleep(0.1)
        st.session_state.ph_stat.empty()
        time.sleep(0.1)
        st.session_state.ph_stat.empty()
        time.sleep(0.1)
