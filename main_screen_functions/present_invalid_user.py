import streamlit as st

from present_stats import add_description


def present_invalid_user() -> None:
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        st.title("Statistics")
        st.write("No such user! Enter a new user name!")
        st.write("Use the sidebar on the left! Click the tiny arrow in the top left corner to open it.")
        st.write("")
        add_description(title="intro", method="description")
    return None
