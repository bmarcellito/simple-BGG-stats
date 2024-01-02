import streamlit as st


def contact_form() -> None:
    ph_contact = st.empty()
    if ph_contact.button("Send feedback!"):
        st.session_state.previous_user_state = st.session_state.user_state
        st.session_state.user_state = "Contact_form"
