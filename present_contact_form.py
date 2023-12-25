import streamlit as st


def send_feedback() -> None:
    st.session_state.user_state = "Contact_form_sent"


def present_contact_sent() -> None:
    st.title("Contact form sent")
    st.write('Thank you!')
    if st.button('Back to the statistics!'):
        st.session_state.user_state = st.session_state.previous_user_state
        st.rerun()


def present_contact_form() -> None:
    st.title("Contact form")
    txt = st.text_area("Give us feedback!")
    if st.button(label='Send your feedback'):
        print(txt)
        st.session_state.user_state = "Contact_form_sent"
        st.rerun()
    if st.button('Later, back to the statistics'):
        st.session_state.user_state = st.session_state.previous_user_state
        st.rerun()
