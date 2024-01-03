from time import sleep
import streamlit as st


def clear_ph_element(element) -> None:
    element.empty()
    sleep(0.1)
    # element.empty()
    # sleep(0.1)


def presentation_hack() -> None:
    st.markdown("""
                    <html><head><style>
                            ::-webkit-scrollbar {width: 14px; height: 14px;}
                    </style></head><body></body></html>
                """, unsafe_allow_html=True)
