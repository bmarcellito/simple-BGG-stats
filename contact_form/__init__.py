import streamlit as st
import pandas as pd

from my_gdrive.save_functions import save_background
from main_screen_functions.presentation_hack import clear_ph_element


def contact_form_button(main_screen) -> None:
    def contact_button_pushed(el_main_screen) -> None:
        st.session_state.app_state = "Contact_form"
        st.session_state.contact_form_state = "Init"
        clear_ph_element([el_main_screen])

    st.button(label="Send feedback!", on_click=contact_button_pushed, args=[main_screen])


def present_contact_sent(main_screen) -> None:
    def thx_button_pushed(el_main_screen) -> None:
        st.session_state.app_state = "User_view"
        clear_ph_element([el_main_screen])

    st.title("Contact form sent")
    st.write('Thank you!')
    st.button(label='Back to the statistics!', on_click=thx_button_pushed, args=[main_screen])


def present_contact_form(main_screen) -> None:
    def send_button_pushed(el_main_screen) -> None:
        ph_save = st.empty()
        with ph_save.status("Saving feedback... please wait"):
            df = pd.DataFrame(data={"name": name, "user_email": email, "feedback": txt}, index=[0])
            save_background(parent_folder="folder_processed", filename="feedbacks", df=df, concat=["feedback"])
            st.session_state.contact_form_state = "Sent"
        del df
        ph_save.empty()
        clear_ph_element([el_main_screen])

    def later_button_pushed(el_main_screen) -> None:
        st.session_state.app_state = "User_view"
        clear_ph_element([el_main_screen])

    st.title("Contact form")
    name = st.text_input('Enter your name (optional)')
    email = st.text_input('E-mail address (optional)')
    txt = st.text_area("Give us feedback!")
    st.button(label='Send your feedback', on_click=send_button_pushed, args=[main_screen])
    st.button(label='Later, back to the statistics', on_click=later_button_pushed, args=[main_screen])


def contact_form(main_screen) -> None:
    if "contact_form_state" not in st.session_state:
        st.session_state.contact_form_state = "Init"
    match st.session_state.contact_form_state:
        case "Init":
            present_contact_form(main_screen)
        case "Sent":
            present_contact_sent(main_screen)
    return None
