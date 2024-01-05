from time import sleep
import streamlit as st
import gc


def clear_ph_element(element_list) -> None:
    for element in element_list:
        element.empty()
        sleep(0.1)
    gc.collect()


def presentation_hack() -> None:
    st.markdown("""
                    <html><head><style>
                            ::-webkit-scrollbar {width: 14px; height: 14px;}
                    </style></head><body></body></html>
                """, unsafe_allow_html=True)
