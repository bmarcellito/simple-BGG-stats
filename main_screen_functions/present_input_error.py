import streamlit as st


def present_input_error() -> None:
    with st.container():
        st.title("Error while importing user information")
        st.write("Please try it later!")
    return None
