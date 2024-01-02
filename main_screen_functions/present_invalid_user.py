import streamlit as st

from present_stats import add_description


def present_invalid_user() -> None:
    with st.container():
        st.title("User not found!")
        st.write("Enter a new user name!")
        st.write("Use the sidebar on the left! Don't see it? Click the tiny arrow in the top left corner to open it.")
        st.write("")
        add_description(title="intro", method="description")
    return None
