import streamlit as st
import pandas as pd

from my_gdrive.save_functions import save_background


def contact_form_button() -> None:
    if st.button(label="Send feedback!"):
        st.session_state.previous_user_state = st.session_state.user_state
        st.session_state.user_state = "Contact_form"
        st.session_state.contact_form_state = "Init"


def present_contact_sent() -> None:
    st.title("Contact form sent")
    st.write('Thank you!')
    if st.button('Back to the statistics!'):
        st.session_state.user_state = st.session_state.previous_user_state
        st.rerun()


def present_contact_form() -> None:
    st.title("Contact form")
    name = st.text_input('Enter your name (optional)')
    email = st.text_input('E-mail address (optional)')
    txt = st.text_area("Give us feedback!")
    if st.button(label='Send your feedback'):
        df = pd.DataFrame(data={"name": name, "user_email": email, "feedback": txt}, index=[0])
        save_background(parent_folder="folder_processed", filename="feedbacks", df=df, concat=["feedback"])
        st.session_state.contact_form_state = "Sent"
        st.rerun()
    if st.button('Later, back to the statistics'):
        st.session_state.user_state = st.session_state.previous_user_state
        st.rerun()


def contact_form() -> None:
    if "contact_form_state" not in st.session_state:
        st.session_state.contact_form_state = "Init"
    match st.session_state.contact_form_state:
        case "Init":
            present_contact_form()
        case "Sent":
            present_contact_sent()
    return None
