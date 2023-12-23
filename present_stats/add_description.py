import pandas as pd
import streamlit as st


@st.cache_data()
def add_description(title: str, method="explanation") -> None:
    df = pd.read_csv("present_stats/stat_desc.csv", index_col="topic")
    text_to_show = df.at[title, "description"]
    match method:
        case "explanation":
            with st.expander("See explanation"):
                st.markdown(text_to_show)
        case "description":
            st.write(text_to_show)
    return None


