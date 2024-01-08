import streamlit as st


def present_input_error(error_msg: str) -> None:
    with st.container():
        st.title(error_msg)
        st.write("Please try it later!")
    return None
