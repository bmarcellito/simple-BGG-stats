import streamlit as st

from present_stats import add_description


def present_starting_screen() -> None:
    with st.container():
        st.title("Statistics from BoardGameGeek.com")
        st.write("Enter a user name first!")
        st.write("Use the sidebar on the left! Don't see it? Click the tiny arrow in the top left corner to open it.")
        st.write("")
        add_description(title="intro", method="description")
    return None
